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
	def makeLayout(self,nCaptionLines,rowEntries,colEntries,staticColStyles,amountColStyles):
		# mainly, number of entries is needed
		# but names can be used, for example, in html col classes for styling
		# should return Layout object
		raise NotImplementedError
	def save(self):
		raise NotImplementedError

class XlsxSpreadsheet(Spreadsheet):
	def __init__(self,filename):
		super().__init__(filename)
		import xlsxwriter
		self.wb=xlsxwriter.Workbook(self.filename)
		self.ws=self.wb.add_worksheet('expenditures')
	def makeLayout(self,nCaptionLines,rowEntries,colEntries,staticColStyles,amountColStyles):
		ws=self.ws
		amountStyle=self.wb.add_format({'num_format':'#,##0.0;-#,##0.0;""'})
		class XlsxLayout(Layout):
			def __init__(self):
				r0=nCaptionLines+len(colEntries)
				c0=0
				ws.freeze_panes(r0,0)
			def setColWidth(self,c,width):
				ws.set_column(c,c,width)
			def setColWidthAndLevel(self,c,width,level):
				ws.set_column(c,c,width=width,options={'level':level})
			def write(self,r,c,value):
				ws.write(r,c,value)
			def writeRange(self,r1,c1,r2,c2,value):
				if c1!=c2 or r1!=r2:
					ws.merge_range(r1,c1,r2,c2,value)
				else:
					ws.write(r1,c1,value)
			# candidates for superclass
			def writeStaticHeaders(self,staticHeaders):
				def width(style):
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
				r0=nCaptionLines
				c0=0
				r1=r0+len(colEntries)-1
				for c,(value,style) in enumerate(zip(staticHeaders,staticColStyles)):
					w=width(style)
					if w:
						self.setColWidth(c,w)
					self.writeRange(r0,c0+c,r1,c0+c,value)
			def writeRowHeaders(self,rowHeaders):
				r0=nCaptionLines+len(colEntries)
				c0=0
				for r,(level,values) in enumerate(rowHeaders):
					ws.set_row(r0+r,options={'level':level})
					for c,value in enumerate(values):
						self.write(r0+r,c0+c,value)
			def writeColHeaders(self,colHeaders):
				r0=nCaptionLines
				c0=len(rowEntries)
				noneValues=tuple(None for _ in colEntries)
				oldValues=noneValues
				nRepeats=[0 for _ in colEntries]
				for c,(level,values) in enumerate(itertools.chain(colHeaders,((-1,noneValues),))):
					if level>=0:
						self.setColWidthAndLevel(c0+c,12,level) # FIXME 12 = width for amount
					for r,value in enumerate(values):
						if values[:r+1]!=oldValues[:r+1] and oldValues[r]!=None:
							self.writeRange(r0+r,c0+c-nRepeats[r],r0+r,c0+c-1,oldValues[r])
							nRepeats[r]=1
						else:
							nRepeats[r]+=1
					oldValues=values
			def writeAmount(self,r,c,amount):
				r0=nCaptionLines+len(colEntries)
				c0=len(rowEntries)
				ws.write_number(r0+r,c0+c,amount,amountStyle)
			def getCellName(self,r,c):
				r0=nCaptionLines+len(colEntries)
				c0=len(rowEntries)
				a=ord('A')
				radix=ord('Z')-a+1
				if c0+c<radix:
					cn=chr(a+c0+c)
				else:
					cn=chr(a+(c0+c)//radix-1)+chr(a+(c0+c)%radix)
				return cn+str(r0+r+1)
			def writeRowSum(self,r,c,amount,c1,c2,cs,isLowestLevel):
				r0=nCaptionLines+len(colEntries)
				c0=len(rowEntries)
				if isLowestLevel:
					formula='=SUM('+self.getCellName(r,c1)+':'+self.getCellName(r,c2)+')'
				else:
					formula='='+'+'.join(self.getCellName(r,cc) for cc in cs)
				ws.write_formula(r0+r,c0+c,formula,amountStyle,amount)
			def writeColSum(self,r,c,amount,r1,r2,rs,isLowestLevel):
				r0=nCaptionLines+len(colEntries)
				c0=len(rowEntries)
				formula='=SUBTOTAL(9,'+self.getCellName(r1,c)+':'+self.getCellName(r2,c)+')'
				ws.write_formula(r0+r,c0+c,formula,amountStyle,amount)
		return XlsxLayout()
	def save(self):
		self.wb.close()
