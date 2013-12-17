class Report:
	def __init__(self,sqlConn,rows,cols):
		# TODO specify filter
		self.rows=rows
		self.cols=cols
		self.rowsData=self.rows.getData(sqlConn)
		self.colsData=self.cols.getData(sqlConn)
		# qg=','.join(self.rows.listKeyEntries()+self.cols.listKeyEntries())
		# q='SELECT '+qg+',SUM(amount) AS amount\n'
		# q+='FROM items\n'
		# q+='GROUP BY '+qg
		# print(q)
		# for item in sqlConn.execute(q):
			# print(item)
	def save(self,spreadsheet):
		layout=spreadsheet.makeLayout(1,self.rows.listEntries(),self.cols.listEntries())
		layout.writeRowHeaders(self.rowsData)
		layout.writeColHeaders(self.colsData)
		spreadsheet.save()
