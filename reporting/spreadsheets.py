import itertools

class Layout:
	def writeRowHeaders(self,rowHeaders):
		raise NotImplementedError
	def writeColHeaders(self,colHeaders):
		raise NotImplementedError
	def writeAmount(self,r,c,amount):
		raise NotImplementedError
	def writeRowSum(self,r,c,amount,c1,c2,cs,isLowestLevel):
		raise NotImplementedError
	def writeColSum(self,r,c,amount,r1,r2,rs,isLowestLevel):
		raise NotImplementedError

class Spreadsheet:
	def __init__(self,filename):
		self.filename=filename
	def makeLayout(self,nCaptionLines,nRowEntries,nColEntries,nRowLevels,staticColStyles,amountColStyles):
		raise NotImplementedError
	def save(self):
		raise NotImplementedError

class XlsxSpreadsheet(Spreadsheet):
	def __init__(self,filename):
		super().__init__(filename)
		import xlsxwriter
		self.wb=xlsxwriter.Workbook(self.filename)
		self.ws=self.wb.add_worksheet('expenditures')
	def makeLayout(self,nCaptionLines,nRowEntries,nColEntries,nRowLevels,staticColStyles,amountColStyles):
		ws=self.ws
		def makeFormat(props):
			normalFormat=self.wb.add_format(props)
			boldFormat=self.wb.add_format(dict((('bold',True),)+tuple(props.items())))
			def isBold(level):
				return level<nRowLevels//2
			def format(level):
				return boldFormat if isBold(level) else normalFormat
			return format
		textFormat=makeFormat({})
		codeFormat=makeFormat({'align':'center'})
		absoluteAmountFormat=makeFormat({'num_format':'#,##0.0;-#,##0.0;""'})
		relativeAmountFormat=makeFormat({'num_format':'+#,##0.0;-#,##0.0;""'})
		headerFormat=self.wb.add_format({'bold':True,'text_wrap':True})
		codeHeaderFormat=self.wb.add_format({'bold':True,'font_size':9,'text_wrap':True})
		captionFormat=self.wb.add_format({'bold':True,'font_size':13})
		class XlsxLayout(Layout):
			def __init__(self):
				r0=nCaptionLines+nColEntries
				c0=0
				ws.freeze_panes(r0,0)
			def setColWidth(self,c,width):
				ws.set_column(c,c,width)
			def setColWidthAndLevel(self,c,width,level):
				ws.set_column(c,c,width=width,options={'level':level})
			def write(self,r,c,value,format=None):
				ws.write(r,c,value,format)
			def writeRange(self,r1,c1,r2,c2,value,format=None):
				if c1!=c2 or r1!=r2:
					ws.merge_range(r1,c1,r2,c2,value,format)
				else:
					ws.write(r1,c1,value,format)
			# candidates for superclass
			def writeCaption(self,caption):
				self.writeRange(0,0,0,nRowEntries-1,caption,captionFormat)
			def writeStaticHeaders(self,staticHeaders):
				def width(c):
					style=staticColStyles[c]
					if 'name' in style:
						return 100
					elif 'department' in style:
						return 4
					elif 'section' in style:
						return 5
					elif 'category' in style:
						return 8
					elif 'type' in style:
						return 4
					# elif 'amount' in style:
						# return 12 # set in writeColHeaders
				def format(c):
					style=staticColStyles[c]
					if 'code' in style:
						return codeHeaderFormat
					else:
						return headerFormat
				r0=nCaptionLines
				c0=0
				r1=r0+nColEntries-1
				for c,value in enumerate(staticHeaders):
					w=width(c)
					if w:
						self.setColWidth(c,w)
					self.writeRange(r0,c0+c,r1,c0+c,value,format(c))
				for r in range(nColEntries):
					ws.set_row(r0+r,60//nColEntries)
			def writeRowHeaders(self,rowHeaders):
				def format(c):
					if 'code' in staticColStyles[c]:
						return codeFormat
					else:
						return textFormat
				r0=nCaptionLines+nColEntries
				c0=0
				for r,(level,values) in enumerate(rowHeaders):
					ws.set_row(r0+r,options={'level':level})
					for c,value in enumerate(values):
						self.write(r0+r,c0+c,value,format(c)(level))
			def writeColHeaders(self,colHeaders):
				r0=nCaptionLines
				c0=nRowEntries
				noneValues=(None,)*nColEntries
				oldValues=noneValues
				nRepeats=[0]*nColEntries
				for c,(level,values) in enumerate(itertools.chain(colHeaders,((-1,noneValues),))):
					if level>=0:
						self.setColWidthAndLevel(c0+c,12,level) # FIXME 12 = width for amount
					for r,value in enumerate(values):
						if values[:r+1]!=oldValues[:r+1] and oldValues[r]!=None:
							self.writeRange(r0+r,c0+c-nRepeats[r],r0+r,c0+c-1,oldValues[r],headerFormat)
							nRepeats[r]=1
						else:
							nRepeats[r]+=1
					oldValues=values
				self.writeRange(0,nRowEntries,0,nRowEntries+c-1,"(тыс. руб.)")
			def getAmountFormat(self,c):
				if 'relative' in amountColStyles[c]:
					return relativeAmountFormat
				else:
					return absoluteAmountFormat
			def writeAmount(self,r,c,amount):
				r0=nCaptionLines+nColEntries
				c0=nRowEntries
				level=nRowLevels-1
				ws.write_number(r0+r,c0+c,amount,self.getAmountFormat(c)(level))
			def getCellName(self,r,c):
				r0=nCaptionLines+nColEntries
				c0=nRowEntries
				a=ord('A')
				radix=ord('Z')-a+1
				if c0+c<radix:
					cn=chr(a+c0+c)
				else:
					cn=chr(a+(c0+c)//radix-1)+chr(a+(c0+c)%radix)
				return cn+str(r0+r+1)
			def writeRowSum(self,r,c,amount,c1,c2,cs,level,isDeepestSum):
				level=nRowLevels-1 # discard col level
				r0=nCaptionLines+nColEntries
				c0=nRowEntries
				if isDeepestSum:
					formula='=SUM('+self.getCellName(r,c1)+':'+self.getCellName(r,c2)+')'
				else:
					formula='='+'+'.join(self.getCellName(r,cc) for cc in cs)
				ws.write_formula(r0+r,c0+c,formula,self.getAmountFormat(c)(level),amount)
			def writeColSum(self,r,c,amount,r1,r2,rs,level,isDeepestSum):
				r0=nCaptionLines+nColEntries
				c0=nRowEntries
				formula='=SUBTOTAL(9,'+self.getCellName(r1,c)+':'+self.getCellName(r2,c)+')'
				ws.write_formula(r0+r,c0+c,formula,self.getAmountFormat(c)(level),amount)
		return XlsxLayout()
	def save(self):
		self.wb.close()
