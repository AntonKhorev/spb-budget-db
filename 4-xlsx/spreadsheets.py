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
		def isBold(level):
			return level<nRowLevels//2
		def makeFormat(props):
			normalFormat=self.wb.add_format(props)
			boldFormat=self.wb.add_format(dict((('bold',True),)+tuple(props.items())))
			def format(level):
				return boldFormat if isBold(level) else normalFormat
			return format
		def makeNameFormat():
			formats=[]
			for i in range(7): # max # of levels
				format=self.wb.add_format()
				if isBold(i):
					format.set_bold()
				format.set_indent(i)
				formats.append(format)
			def formatFn(level):
				return formats[level]
			return formatFn
		textFormat=makeFormat({})
		nameFormat=makeNameFormat()
		codeFormat=makeFormat({'align':'center'})
		absoluteAmountFormat=makeFormat({'num_format':'[>=0.05]#,##0.0;[<=-0.05]−#,##0.0;;@'})

		# COLORx won't work
		# COLOR4 = dark green in LibreOffice, light green (bad) in Excel Viewer
		# COLOR6 = dark red in LibreOffice, yellow (very bad) in Excel Viewer
		# relativeAmountFormat=makeFormat({'num_format':'[COLOR4]+#,##0.0;[COLOR6]−#,##0.0;""'})
		# relativeAmountFormat=makeFormat({'num_format':'[COLOR58]+#,##0.0;[COLOR30]−#,##0.0;""'}) # doesn't work in Excel Viewer at all
		# relativeAmountFormat=makeFormat({'num_format':'+#,##0.0;−#,##0.0;""'})
		relativeAmountFormat=makeFormat({'num_format':'[>=0.05]+#,##0.0;[RED][<=-0.05]−#,##0.0;;[BLACK]@','font_color':'#004400'})

		# conditional format
		# positiveRelativeAmountFormat=self.wb.add_format({'font_color':'#004400'})
		# negativeRelativeAmountFormat=self.wb.add_format({'font_color':'#440000'})

		headerFormat=self.wb.add_format({'bold':True,'text_wrap':True})
		codeHeaderFormat=self.wb.add_format({'bold':True,'font_size':9,'text_wrap':True})
		captionFormat=self.wb.add_format({'bold':True,'font_size':13})
		class XlsxLayout(Layout):
			def __init__(self):
				r0=nCaptionLines+nColEntries
				c0=0
				ws.freeze_panes(r0,0)
				ws.outline_settings(True,False,True,False)
				# conditional format - too slow, buggy in LibreOffice
				# ws.conditional_format('K4:K17',{
					# 'type':'cell',
					# 'criteria':'>',
					# 'value':0,
					# 'format':positiveRelativeAmountFormat,
				# })
				# ws.conditional_format('K4:K17',{
					# 'type':'cell',
					# 'criteria':'<',
					# 'value':0,
					# 'format':negativeRelativeAmountFormat,
				# })
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
			def writeComment(self,r,c,comment):
				nLines=0
				maxLen=0
				for line in comment.split('\n'):
					nLines+=1
					maxLen=max((maxLen,len(line)))
				ws.write_comment(r,c,comment,{
					'width':6*maxLen,
					'height':15*nLines,
				})
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
				# set height of rows for column headers/subheaders
				headerRowHeights=[30 if r==1 else 15 for r in range(nColEntries)]
				minSumHeight=40 # minimal height for category/type/etc headers to fit
				if sum(headerRowHeights)<minSumHeight:
					headerRowHeights[-1]+=minSumHeight-sum(headerRowHeights)
				for r in range(nColEntries):
					ws.set_row(r0+r,headerRowHeights[r])
			def writeRowHeaders(self,rowHeaders):
				def format(c):
					if 'code' in staticColStyles[c]:
						return codeFormat
					elif 'name' in staticColStyles[c]:
						return nameFormat
					else:
						return textFormat
				r0=nCaptionLines+nColEntries
				c0=0
				for r,(level,values,comments) in enumerate(rowHeaders):
					ws.set_row(r0+r,options={'level':level})
					for c,value in enumerate(values):
						self.write(r0+r,c0+c,value,format(c)(level))
			def writeColHeaders(self,colHeaders):
				r0=nCaptionLines
				c0=nRowEntries
				noneValues=(None,)*nColEntries
				oldValues=noneValues
				oldComments=noneValues
				nRepeats=[0]*nColEntries
				for c,(level,values,comments) in enumerate(itertools.chain(colHeaders,((-1,noneValues,noneValues),))):
					if level>=0:
						self.setColWidthAndLevel(c0+c,12,level) # FIXME 12 = width for amount
					for r,value in enumerate(values):
						if values[:r+1]!=oldValues[:r+1] and oldValues[r]!=None:
							self.writeRange(r0+r,c0+c-nRepeats[r],r0+r,c0+c-1,oldValues[r],headerFormat)
							if oldComments and oldComments[r] is not None:
								self.writeComment(r0+r,c0+c-nRepeats[r],oldComments[r])
							nRepeats[r]=1
						else:
							nRepeats[r]+=1
					oldValues=values
					oldComments=comments
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
