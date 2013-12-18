import itertools

class LinesData:
	def __init__(self,levelOrders,amountsKey):
		self.levelOrders=levelOrders
		self.amountsKey=amountsKey
		self.lineList=[] # [(level,values),...]
		self.amountMap={} # {amountsKey:lineNumber,...}
	def addLine(self,level,key,values):
		amountsLevel=len(self.levelOrders)-1
		if level==amountsLevel:
			self.amountMap[key]=len(self.lineList)
		self.lineList.append((level,values))
	def computeTree(self):
		self.lineTreeNodes=[None for _ in self.lineList]
		self.lineTreeRoots=[]
		amountsLevel=len(self.levelOrders)-1
		# TODO inefficient version - rewrite
		def rec(level,minLine,maxLine):
			if level==amountsLevel:
				return
			children=[]
			if self.levelOrders[level]==Lines.BEFORE:
				assert self.lineList[minLine][0]==level
				for l in range(maxLine,minLine-1,-1):
					if self.lineList[l][0]==level+1:
						children.insert(0,l)
					elif self.lineList[l][0]==level:
						self.lineTreeNodes[l]=[l+1,maxLine,children]
						if level==0:
							self.lineTreeRoots.insert(0,l)
						rec(level+1,l+1,maxLine)
						children=[]
						maxLine=l-1
			else:
				assert self.lineList[maxLine][0]==level
				for l in range(minLine,maxLine+1):
					if self.lineList[l][0]==level+1:
						children.append(l)
					elif self.lineList[l][0]==level:
						self.lineTreeNodes[l]=[minLine,l-1,children]
						if level==0:
							self.lineTreeRoots.append(l)
						rec(level+1,minLine,l-1)
						children=[]
						minLine=l+1
		rec(0,0,len(self.lineList)-1)
		print('roots:',self.lineTreeRoots)
		print('nodes{')
		for l,n in enumerate(self.lineTreeNodes):
			print(l,':',n)
		print('}nodes')
	def listLines(self):
		return self.lineList
	def getLineForAmountItem(self,item):
		return self.amountMap[tuple(item[k] for k in self.amountsKey)]

class Lines:
	BEFORE=1
	AFTER=2
	def listEntries(self):
		raise NotImplementedError
	def listLevelOrders(self):
		# order for final level should be BEFORE
		raise NotImplementedError
	def listLevelKeys(self):
		raise NotImplementedError
	def getItemValues(self,item,level):
		raise NotImplementedError
	def listQuerySelects(self):
		raise NotImplementedError
	def listQueryOrderbys(self):
		raise NotImplementedError
	def getAmountsKey(self):
		return self.listLevelKeys()[-1]
	def listItemLevelKeys(self,item):
		return [tuple(item[k] for k in levelKey) for levelKey in self.listLevelKeys()]
	def getData(self,sqlConn):
		# TODO store/return key->line# map
		levelOrders=self.listLevelOrders()
		data=LinesData(levelOrders,self.getAmountsKey())
		noneKeys=[None for _ in levelOrders]
		oldItem=None
		oldLevelKeys=noneKeys
		for item in itertools.chain(
			sqlConn.queryHeaders(
				self.listQuerySelects(),
				self.listQueryOrderbys()
			),
			(None,)
		):
			if item is None:
				levelKeys=noneKeys
			else:
				levelKeys=self.listItemLevelKeys(item)
			reset=False
			for level,levelKey in enumerate(levelKeys):
				if reset or levelKey!=oldLevelKeys[level]:
					reset=True
					if levelOrders[level]==self.BEFORE and item is not None:
						data.addLine(level,levelKey,self.getItemValues(item,level))
					elif levelOrders[level]==self.AFTER and oldItem is not None:
						data.addLine(level,oldLevelKeys[level],self.getItemValues(oldItem,level))
			oldItem=item
			oldLevelKeys=levelKeys
		data.computeTree()
		return data

class DepartmentRows(Lines):
	def listEntries(self):
		return [
			'name',
			'departmentCode',
			'sectionCode',
			'categoryCode',
			'typeCode',
		]
	def listLevelOrders(self):
		return [
			self.AFTER,
			self.BEFORE,
			self.BEFORE,
			self.BEFORE,
		]
	def listLevelKeys(self):
		return [
			tuple(),
			('departmentCode',),
			('departmentCode','sectionCode','categoryCode'),
			('departmentCode','sectionCode','categoryCode','typeCode'),
		]
	def getItemValues(self,item,level):
		if level==0:
			return ('Итого',)
		elif level==1:
			return (item['departmentName'],item['departmentCode'])
		elif level==2:
			return (item['categoryName'],item['departmentCode'],item['sectionCode'],item['categoryCode'])
		elif level==3:
			return (item['typeName'],item['departmentCode'],item['sectionCode'],item['categoryCode'],item['typeCode'])
		raise ValueError()
	def listQuerySelects(self):
		return (
			'departmentCode','sectionCode','categoryCode','typeCode',
			'departmentName',              'categoryName','typeName'
		)
	def listQueryOrderbys(self):
		return 'departmentOrder','sectionCode','categoryCode','typeCode'

class SectionRows(Lines):
	def listEntries(self):
		return [
			'name',
			'sectionCode',
			'categoryCode',
			'typeCode',
		]
	def listLevelOrders(self):
		return [
			self.AFTER,
			self.BEFORE,
			self.BEFORE,
			self.BEFORE,
			self.BEFORE,
		]
	def listLevelKeys(self):
		return [
			tuple(),
			('superSectionCode',),
			('sectionCode',),
			('sectionCode','categoryCode'),
			('sectionCode','categoryCode','typeCode'),
		]
	def getItemValues(self,item,level):
		if level==0:
			return ('Итого',)
		elif level==1:
			return (item['superSectionName'],item['superSectionCode'])
		elif level==2:
			return (item['sectionName'],item['sectionCode'])
		elif level==3:
			return (item['categoryName'],item['sectionCode'],item['categoryCode'])
		elif level==4:
			return (item['typeName'],item['sectionCode'],item['categoryCode'],item['typeCode'])
		raise ValueError()
	def listQuerySelects(self):
		return (
			'superSectionCode','sectionCode','categoryCode','typeCode',
			'superSectionName','sectionName','categoryName','typeName'
		)
	def listQueryOrderbys(self):
		return 'superSectionCode','sectionCode','categoryCode','typeCode'

class AmendmentCols(Lines):
	def listEntries(self):
		return [
			'year',
			'documentNumber',
		]
	def listLevelOrders(self):
		return [
			self.AFTER,
			self.BEFORE,
		]
	def listLevelKeys(self):
		return [
			('year',),
			('year','documentNumber'),
		]
	def getItemValues(self,item,level):
		if level==0:
			return (str(item['year'])+' г.','Итого (тыс. руб.)')
		elif level==1:
			return (str(item['year'])+' г.','Изменения в док. '+str(item['documentNumber'])+ ' (тыс. руб.)')
		raise ValueError()
	def listQuerySelects(self):
		return 'year','documentNumber'
	def listQueryOrderbys(self):
		return 'year','documentNumber'
