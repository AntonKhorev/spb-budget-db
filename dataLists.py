import decimal
import collections

class AbstractList:
	def __init__(self):
		self.names={}
		self.priorities={}
		self.nameCollisions=collections.defaultdict(set)
	def add(self,row,priority):
		code=row[self.codeCol]
		name=row[self.nameCol]
		if code in self.names:
			if self.names[code]!=name:
				if priority<self.priorities[code]:
					print('- priority = '+str(self.priorities[code])+'; '+self.codeCol+' = '+code+'; '+self.nameCol+' = '+str(self.names[code]))
					self.names[code]=name
					self.priorities[code]=priority
					print('+ priority = '+str(self.priorities[code])+'; '+self.codeCol+' = '+code+'; '+self.nameCol+' = '+str(self.names[code]))
				elif name not in self.nameCollisions[code]:
					print('c priority = '+str(priority)+'; '+self.codeCol+' = '+code+'; '+self.nameCol+' = '+str(name))
					print('+ priority = '+str(self.priorities[code])+'; '+self.codeCol+' = '+code+'; '+self.nameCol+' = '+str(self.names[code]))
				self.nameCollisions[code].add(name)
		else:
			self.names[code]=name
			self.priorities[code]=priority
	def getOrderedRows(self):
		for code,name in sorted(self.names.items()):
			yield {self.codeCol:code,self.nameCol:name}
	def getCodeForName(self,name):
		for c,n in self.names.items():
			if n.lower()==name.lower():
				return c
		raise Exception('unknown name: '+name)

class DepartmentList(AbstractList):
	def __init__(self):
		super().__init__()
		self.codeCol='departmentCode'
		self.nameCol='departmentName'
		self.vertices=collections.defaultdict(set)
		self.prevCode=None
	def resetSequence(self):
		self.prevCode=None
	def add(self,row,priority):
		super().add(row,priority)
		code=row[self.codeCol]
		if self.prevCode is not None:
			if self.prevCode==code:
				return
			self.vertices[self.prevCode].add(code)
		self.prevCode=code
	def getOrderedRows(self):
		exitSeq=[]
		grayVertices=set()
		blackVertices=set()
		def dfs(vertex):
			if vertex in blackVertices:
				return
			if vertex in grayVertices:
				raise Exception('conflicting order of departments')
			grayVertices.add(vertex)
			for nextVertex in self.vertices[vertex]:
				dfs(nextVertex)
			grayVertices.remove(vertex)
			blackVertices.add(vertex)
			exitSeq.append(vertex)
		for vertex in self.names:
			dfs(vertex)
		for order,code in enumerate(reversed(exitSeq)):
			yield {'departmentCode':code,'departmentName':self.names[code],'departmentOrder':order}

class SuperSectionList(AbstractList):
	def __init__(self):
		super().__init__()
		self.codeCol='superSectionCode'
		self.nameCol='superSectionName'

class SectionList(AbstractList):
	def __init__(self):
		super().__init__()
		self.codeCol='sectionCode'
		self.nameCol='sectionName'
	def getOrderedRows(self):
		for code,name in sorted(self.names.items()):
			yield {self.codeCol:code,'superSectionCode':code[:2]+'00',self.nameCol:name}

class CategoryList(AbstractList):
	def __init__(self):
		super().__init__()
		self.codeCol='categoryCode'
		self.nameCol='categoryName'

class TypeList(AbstractList):
	def __init__(self):
		super().__init__()
		self.codeCol='typeCode'
		self.nameCol='typeName'

class ItemList:
	keyCols=('year','departmentCode','sectionCode','categoryCode','typeCode')
	def __init__(self):
		# (year,departmentCode,sectionCode,categoryCode,typeCode) -> editNumber)-> decimal amount
		self.items=collections.defaultdict(lambda: collections.defaultdict(decimal.Decimal))
		# TODO save running sum to make it faster
		# TODO clean up zeros to make it faster
	def rowKey(self,row):
		return tuple(row[k] for k in self.keyCols)
	def rowValue(self,row):
		return decimal.Decimal(row['amount'])
	def keySum(self,k):
		return sum(self.items[k].values())
	def rowSum(self,row):
		return self.keySum(self.rowKey(row))
	def add(self,row,editNumber):
		self.items[self.rowKey(row)][editNumber]+=self.rowValue(row)
	def makeSetContext(self,editNumber,years):
		class SetContext:
			def __init__(self,itemList):
				self.itemList=itemList
			def __enter__(self):
				# self.editNumber=None
				self.residuals=collections.defaultdict(decimal.Decimal)
				for k in self.itemList.items:
					if k[0] in years:
						self.residuals[k]=self.itemList.keySum(k)
				return self
			def set(self,row):
				k=self.itemList.rowKey(row)
				if k[0] not in years:
					raise Exception('year '+str(k[0])+' in context for years '+str(years))
				self.itemList.items[k][editNumber]+=self.itemList.rowValue(row)-self.residuals[k]
				del self.residuals[k]
			def __exit__(self,exc_type,exc_value,traceback):
				for k,v in self.residuals.items():
					self.itemList.items[k][editNumber]-=v
		return SetContext(self)
	def makeDiffsetContext(self,editNumber,startEditNumber,years):
		# TODO remove copypaste
		class DiffsetContext:
			def __init__(self,itemList):
				self.itemList=itemList
			def __enter__(self):
				# self.editNumber=None
				self.residuals=collections.defaultdict(decimal.Decimal)
				for k in self.itemList.items:
					if k[0] in years:
						self.residuals[k]=sum(v for n,v in self.itemList.items[k].items() if n>=startEditNumber)
				return self
			def set(self,row):
				k=self.itemList.rowKey(row)
				if k[0] not in years:
					raise Exception('year '+str(k[0])+' in context for years '+str(years))
				self.itemList.items[k][editNumber]+=self.itemList.rowValue(row)-self.residuals[k]
				del self.residuals[k]
			def __exit__(self,exc_type,exc_value,traceback):
				for k,v in self.residuals.items():
					self.itemList.items[k][editNumber]-=v
		return DiffsetContext(self)
	def move(self,s,t,editNumber):
		ks=self.rowKey(s)
		kt=self.rowKey(t)
		moves=[]
		for k1 in self.items:
			k2=list(k1)
			for i in range(len(ks)):
				if ks[i]=='*':
					pass
				elif ks[i]==k1[i]:
					k2[i]=kt[i]
				else:
					break
			else:
				k2=tuple(k2)
				moves.append((k1,k2))
		for k1,k2 in moves:
			v=self.keySum(k1)
			self.items[k1][editNumber]-=v
			self.items[k2][editNumber]+=v
	def getOrderedRows(self):
		for k in sorted(self.items):
			for e in sorted(self.items[k]):
				v=self.items[k][e]
				if v:
					yield dict(tuple(zip(self.keyCols,k))+(('editNumber',e),('amount',v)))
