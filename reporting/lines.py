import itertools

class LinesData:
	def __init__(self,amountsLevel,amountsKey):
		self.amountsLevel=amountsLevel
		self.amountsKey=amountsKey
		self.lineList=[] # [(level,values),...]
		self.amountMap={} # {amountsKey:lineNumber,...}
	def addLine(self,level,key,values):
		if level==self.amountsLevel:
			self.amountMap[key]=len(self.lineList)
		self.lineList.append((level,values))
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
		data=LinesData(len(levelOrders)-1,self.getAmountsKey())
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
