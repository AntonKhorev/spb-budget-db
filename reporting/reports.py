class Report:
	def __init__(self,sqlConn,rows,cols):
		# TODO specify filter
		self.rows=rows
		self.cols=cols
		self.rowsData=self.rows.getData(sqlConn)
	def save(self,spreadsheet):
		layout=spreadsheet.makeLayout(1,self.rows.listEntries(),self.cols.listEntries())
		layout.writeRowHeaders(self.rowsData)
		spreadsheet.save()
