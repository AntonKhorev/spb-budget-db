import decimal
import collections

class AbstractList:
	def __init__(self):
		self.names={}
		self.nameCollisions=collections.defaultdict(set)
	def add(self,row):
		code=row[self.codeCol]
		name=row[self.nameCol]
		if code in self.names:
			if self.names[code]!=name and name not in self.nameCollisions[code]:
				self.nameCollisions[code].add(name)
				# raise Exception('code collision: '+self.codeCol+' = '+code+'; '+self.nameCol+' = '+str(self.names[code])+' vs '+str(name))
				print('+ '+self.codeCol+' = '+code+'; '+self.nameCol+' = '+str(self.names[code]))
				print('- '+self.codeCol+' = '+code+'; '+self.nameCol+' = '+str(name))
		else:
			self.names[code]=name
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
	def add(self,row):
		super().add(row)
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

class ItemSums(collections.defaultdict):
	def __init__(self):
		super().__init__(decimal.Decimal) # key=year,departmentCode,sectionCode,categoryCode,typeCode
	def keyToDict(self,k):
		return dict(zip(('year','departmentCode','sectionCode','categoryCode','typeCode'),k))
	def keyToTuple(self,row):
		return tuple(row[k] for k in ('year','departmentCode','sectionCode','categoryCode','typeCode'))
	def add(self,row):
		self[self.keyToTuple(row)]-=decimal.Decimal(row['ydsscctAmount']) # subtract this, then add amount stated in the law
	def fix(self,row):
		self[self.keyToTuple(row)]+=decimal.Decimal(row['ydsscctAmount'])
	def makeMoveItems(self,s,t):
		moves=[]
		for k,v in self.items():
			kd1=self.keyToDict(k)
			kd2=dict(kd1)
			for col in s:
				if s[col]=='*':
					pass
				elif s[col]==kd1[col]:
					kd2[col]=t[col]
				else:
					break
			else:
				moves.append((kd1,kd2))
		for kd1,kd2 in moves:
			k1=self.keyToTuple(kd1)
			k2=self.keyToTuple(kd2)
			amount=self[k1]
			del self[k1]
			self[k2]=amount
			kd1['ydsscctAmount']=amount
			kd2['ydsscctAmount']=-amount
			yield kd1
			yield kd2
