from decimal import Decimal

class Report:
	def __init__(self,sqlConn,rows,cols):
		# TODO specify filter
		self.rows=rows
		self.cols=cols
		self.rowsData=self.rows.getData(sqlConn)
		self.colsData=self.cols.getData(sqlConn)
		nRows=len(self.rowsData.listLines())
		nCols=len(self.colsData.listLines())
		self.grid=[[0 for _ in range(nCols)] for _ in range(nRows)]
		for item in sqlConn.queryAmounts(rows.getAmountsKey()+cols.getAmountsKey()):
			self.grid[self.rowsData.getLineForAmountItem(item)][self.colsData.getLineForAmountItem(item)]=item['amount']
	def save(self,spreadsheet):
		layout=spreadsheet.makeLayout(1,self.rows.listEntries(),self.cols.listEntries())
		layout.writeStaticHeaders(self.rows.listStaticHeaders())
		layout.writeRowHeaders(self.rowsData.listLines())
		layout.writeColHeaders(self.colsData.listLines())
		for r in self.rowsData.listBaseIndices():
			for c in self.colsData.listBaseIndices():
				layout.writeAmount(r,c,Decimal(self.grid[r][c])/1000)
		for c,c1,c2,cs,isLowestLevel in self.colsData.walkSums():
			for r in self.rowsData.listBaseIndices():
				self.grid[r][c]=sum(self.grid[r][cc] for cc in cs)
				layout.writeRowSum(r,c,Decimal(self.grid[r][c])/1000,c1,c2,cs,isLowestLevel)
		for r,r1,r2,rs,isLowestLevel in self.rowsData.walkSums():
			for c in range(len(self.grid[0])):
				self.grid[r][c]=sum(self.grid[rr][c] for rr in rs)
				layout.writeColSum(r,c,Decimal(self.grid[r][c])/1000,r1,r2,rs,isLowestLevel)
		spreadsheet.save()
