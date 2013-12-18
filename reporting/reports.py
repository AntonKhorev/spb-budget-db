class Report:
	def __init__(self,sqlConn,rows,cols):
		# TODO specify filter
		self.rows=rows
		self.cols=cols
		self.rowsData=self.rows.getData(sqlConn)
		self.colsData=self.cols.getData(sqlConn)
		for item in sqlConn.queryAmounts(rows.getAmountsKey()+cols.getAmountsKey()):
			print(dict(item))
	def save(self,spreadsheet):
		layout=spreadsheet.makeLayout(1,self.rows.listEntries(),self.cols.listEntries())
		layout.writeRowHeaders(self.rowsData)
		layout.writeColHeaders(self.colsData)
		spreadsheet.save()
