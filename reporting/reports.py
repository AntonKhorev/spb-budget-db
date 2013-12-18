from decimal import Decimal

class Report:
	def __init__(self,sqlConn,rows,cols):
		# TODO specify filter
		self.rows=rows
		self.cols=cols
		self.rowsData=self.rows.getData(sqlConn)
		self.colsData=self.cols.getData(sqlConn)
		self.amountItems=list(sqlConn.queryAmounts(rows.getAmountsKey()+cols.getAmountsKey()))
	def save(self,spreadsheet):
		layout=spreadsheet.makeLayout(1,self.rows.listEntries(),self.cols.listEntries())
		layout.writeRowHeaders(self.rowsData.listLines())
		layout.writeColHeaders(self.colsData.listLines())
		for item in self.amountItems:
			layout.writeAmount(
				self.rowsData.getLineForAmountItem(item),
				self.colsData.getLineForAmountItem(item),
				Decimal(item['amount'])/1000
			)
		spreadsheet.save()
