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
	def listLines(self):
		return self.lineList
	def listBaseIndices(self):
		amountsLevel=len(self.levelOrders)-1
		return (l for l,(level,_) in enumerate(self.lineList) if level==amountsLevel)
	def getLineForAmountItem(self,item):
		return self.amountMap[tuple(item[k] for k in self.amountsKey)]
	def walkSums(self):
		def rec(line,level):
			isDeepestSum=True
			l1,l2,lChildren=self.lineTreeNodes[line]
			for l in lChildren:
				if self.lineTreeNodes[l]:
					isDeepestSum=False
					yield from rec(l,level+1)
			yield line,l1,l2,lChildren,level,isDeepestSum
		for line in self.lineTreeRoots:
			yield from rec(line,0)
	def listAmountStyles(self):
		# for amount columns - related only to class AmendmentCols
		styles=[]
		first1=first2=True
		for level,_ in self.lineList:
			if level==0:
				styles.append({'amount','absolute'})
				first1=first2=True
			elif level==1:
				if first1:
					styles.append({'amount','absolute'})
				else:
					styles.append({'amount','relative'})
				first1=False
			elif level==2:
				if first1 and first2:
					styles.append({'amount','absolute'})
				else:
					styles.append({'amount','relative'})
				first2=False
			else:
				styles.append({'amount','relative'})
		return styles
class Lines:
	BEFORE=1
	AFTER=2
	def listEntries(self):
		raise NotImplementedError
	def listLevelOrders(self):
		# order for final level should be BEFORE
		raise NotImplementedError
	def listLevelKeys(self):
		# list of
		# 	lists of names of db-columns for each level
		# each level has to form globally unique key
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
	def listStaticHeaders(self):
		heads={
			'name':'Наименование',
			'departmentCode':'Ведомство',
			'superSectionCode':'Надраздел',
			'sectionCode':'Раздел',
			'categoryCode':'Целевая статья',
			'typeCode':'Вид расходов',
		}
		return [heads[k] for k in self.listEntries()]
	def listStaticStyles(self):
		styles={
			'name':{'text','name'},
			'departmentCode':{'code','department'},
			'superSectionCode':{'code','section'},
			'sectionCode':{'code','section'},
			'categoryCode':{'code','category'},
			'typeCode':{'code','type'},
		}
		return [styles[k] for k in self.listEntries()]
	def getData(self,sqlConn):
		# TODO store/return key->line# map
		# TODO build tree in this fn instead of data.computeTree()
		levelOrders=self.listLevelOrders()
		data=LinesData(levelOrders,self.getAmountsKey())
		noneKeys=[None for _ in levelOrders]
		oldItem=None
		oldLevelKeys=noneKeys
		nLevels=len(levelOrders)
		for item in itertools.chain(
			sqlConn.queryHeaders(
				self.listQuerySelects(),
				self.listQueryOrderbys()
			),
			(None,) # sentinel to cause data.addLine() calls in pop phase
		):
			if item is None:
				levelKeys=noneKeys
			else:
				levelKeys=self.listItemLevelKeys(item)

			# drill-down phase
			for diffLevel in range(nLevels):
				if levelKeys[diffLevel]!=oldLevelKeys[diffLevel]:
					break
			else:
				raise Exception('Duplicate key')
			# pop phase
			for level in range(nLevels-1,diffLevel-1,-1):
				if levelOrders[level]==self.AFTER and oldItem is not None:
					data.addLine(level,oldLevelKeys[level],self.getItemValues(oldItem,level))
			# push phase
			for level in range(diffLevel,nLevels):
				if levelOrders[level]==self.BEFORE and item is not None:
					data.addLine(level,levelKeys[level],self.getItemValues(item,level))

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
			self.BEFORE, # self.AFTER,
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
			return ('Всего',)
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
			self.BEFORE, # self.AFTER,
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
			return ('Всего',)
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
			'stageNumber',
			'documentNumber',
		]
	def listLevelOrders(self):
		return [
			self.AFTER,
			self.AFTER,
			self.BEFORE,
		]
	def listLevelKeys(self):
		return [
			('year',),
			('year','stageNumber'),
			('year','stageNumber','documentNumber'),
		]
	def getItemValues(self,item,level):
		if item['year']>2014: # FIXME hack
			yearValue=str(item['year'])+' г. (план)'
		else:
			yearValue=str(item['year'])+' г.'
		if level==0:
			return (yearValue,'Бюджет + изменения','')
		if item['stageNumber']==0:
			stageValue='Первоначальный бюджет'
		else:
			stageValue=str(item['stageNumber'])+'-е изменения'
		if level==1:
			return (yearValue,stageValue,'Итого')
		if level==2:
			if item['amendmentFlag']:
				if item['governorFlag']:
					return (yearValue,stageValue,'+Губернатор')
				else:
					if item['documentNumber']==3850 or item['documentNumber']==4752: # FIXME hack
						return (yearValue,stageValue,'+прочее')
					else:
						return (yearValue,stageValue,'+БФК')
			else:
				return (yearValue,stageValue,'Проект')
		raise ValueError()
	def listQuerySelects(self):
		return 'year','stageNumber','documentNumber','amendmentFlag','governorFlag'
	def listQueryOrderbys(self):
		return 'year','stageNumber','documentNumber'
