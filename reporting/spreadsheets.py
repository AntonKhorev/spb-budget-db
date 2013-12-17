class Layout:
	def writeRowHeaders(self,rowHeaders):
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
		nRowEntries=len(rowEntries)
		ws=self.ws
		class XlsxLayout(Layout):
			def writeRowHeaders(self,rowHeaders):
				for r,(level,values) in enumerate(rowHeaders):
					ws.set_row(r,options={'level':level})
					for c,value in enumerate(values):
						ws.write(r,c,value)
		return XlsxLayout()
	def save(self):
		self.wb.close()
