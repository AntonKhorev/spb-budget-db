class Layout:
	def writeRowHeaders(self,rowHeaders):
		raise NotImplementedError
	def writeColHeaders(self,colHeaders):
		raise NotImplementedError

class Spreadsheet:
	def __init__(self,filename):
		self.filename=filename
	def makeLayout(self,nCaptionLines,rowEntries,colEntries):
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
	def makeLayout(self,nCaptionLines,rowEntries,colEntries):
		ws=self.ws
		class XlsxLayout(Layout):
			def writeRowHeaders(self,rowHeaders):
				r0=nCaptionLines+len(colEntries)
				c0=0
				for r,(level,values) in enumerate(rowHeaders):
					ws.set_row(r0+r,options={'level':level})
					for c,value in enumerate(values):
						ws.write(r0+r,c0+c,value)
			def writeColHeaders(self,colHeaders):
				r0=nCaptionLines
				c0=len(rowEntries)
				for c,(level,values) in enumerate(colHeaders):
					ws.set_column(c0+c,c0+c,options={'level':level})
					for r,value in enumerate(values):
						ws.write(r0+r,c0+c,value)
		return XlsxLayout()
	def save(self):
		self.wb.close()
