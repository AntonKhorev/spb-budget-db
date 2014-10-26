import decimal
import collections

class AbstractList:
	def __init__(self):
		self.names={} # code -> current name
		self.priorities={} # code -> priority of current name
		self.nameCollisions=collections.defaultdict(set) # code -> set of encountered names
	def add(self,row,priority):
		code=row[self.codeCol]
		name=row[self.nameCol]
		if code in self.names:
			if self.names[code]!=name:
				if priority>self.priorities[code]:
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

class AbstractItemList:
	def __init__(self):
		# keyCols -> editNumber -> decimal amount
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
	def getOrderedRows(self):
		for k in sorted(self.items):
			for e in sorted(self.items[k]):
				v=self.items[k][e]
				if v:
					yield dict(tuple(zip(self.keyCols,k))+(('editNumber',e),('amount',v)))
	def getRowsForEdit(self,editNumber):
		e=editNumber
		for k in sorted(self.items):
			if e in self.items[k]:
				v=self.items[k][e]
				if v:
					yield dict(tuple(zip(self.keyCols,k))+(('editNumber',e),('amount',v)))

class ItemList(AbstractItemList):
	def __init__(self):
		self.keyCols=('fiscalYear','departmentCode','sectionCode','categoryCode','typeCode')
		super().__init__()

	class Context:
		def __init__(self,itemList,editNumber,fiscalYears):
			self.itemList=itemList
			self.editNumber=editNumber
			self.fiscalYears=fiscalYears
		def set(self,row):
			k=self.itemList.rowKey(row)
			if k[0] not in self.fiscalYears:
				raise Exception('fiscalYear '+str(k[0])+' in context for fiscalYears '+str(self.fiscalYears))
			self.itemList.items[k][self.editNumber]+=self.itemList.rowValue(row)-self.residuals[k]
			del self.residuals[k]
		def __exit__(self,exc_type,exc_value,traceback):
			for k,v in self.residuals.items():
				self.itemList.items[k][self.editNumber]-=v
	class SetContext(Context):
		def __enter__(self):
			self.residuals=collections.defaultdict(decimal.Decimal)
			for k in self.itemList.items:
				if k[0] in self.fiscalYears:
					self.residuals[k]=self.itemList.keySum(k)
			return self
	class DiffsetContext(Context):
		def __init__(self,itemList,editNumber,startEditNumber,fiscalYears):
			super().__init__(itemList,editNumber,fiscalYears)
			self.startEditNumber=startEditNumber
		def __enter__(self):
			self.residuals=collections.defaultdict(decimal.Decimal)
			for k in self.itemList.items:
				if k[0] in self.fiscalYears:
					self.residuals[k]=sum(v for n,v in self.itemList.items[k].items() if n>=self.startEditNumber)
			return self
	def makeSetContext(self,editNumber,fiscalYears):
		return self.SetContext(self,editNumber,fiscalYears)
	def makeDiffsetContext(self,editNumber,startEditNumber,fiscalYears):
		return self.DiffsetContext(self,editNumber,startEditNumber,fiscalYears)

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

class InterYearItemList(AbstractItemList):
	def __init__(self):
		self.keyCols=('fiscalYear','departmentCode','sectionCode','categoryId','typeCode')
		super().__init__()
	def reset(self,editNumber,fiscalYears):
		residuals=collections.defaultdict(decimal.Decimal)
		for k in self.items:
			if k[0] in fiscalYears:
				residuals[k]=self.keySum(k)
		for k,residual in residuals.items():
			self.items[k][editNumber]-=residual

class InterYearCategoryList:
	def __init__(self,yearSets):
		# can't use categoryName as key b/c one name can have multiple codes at the same time
		nIds=0
		self.categoryIdNames={}
		self.documentCodeIds=collections.defaultdict(dict)
		categoryNameCodeAmounts=collections.defaultdict(lambda: collections.defaultdict(decimal.Decimal)) # categoryName -> categoryCode -> amount
		def getCategoryCodeset():
			c=collections.defaultdict(set)
			for name,codeAmounts in categoryNameCodeAmounts.items():
				c[name]=set(codeAmounts.keys())
			return c
		categoryCodeset2=getCategoryCodeset() # active codes with nonzero amounts
		passiveCategoryCodeset2=getCategoryCodeset() # codes that had nonzero amounts and can reclaim their id if they become active
		documentNumber1=None
		for yearSet in yearSets:
			# reset accumulated amounts
			categoryNameCodeAmounts.clear()
			# group edits by documents
			documentEdits=collections.OrderedDict()
			for edit in yearSet.edits:
				if edit['documentNumber'] not in documentEdits:
					documentEdits[edit['documentNumber']]=[]
				documentEdits[edit['documentNumber']].append(edit['editNumber'])
			# walk over documents
			# for editNumber in range(1,len(yearSet.edits)+1):
			for documentNumber2,editNumbers in documentEdits.items():
				categoryCodeset1=categoryCodeset2
				passiveCategoryCodeset1=passiveCategoryCodeset2
				# compute active category codes = with nonzero amounts
				for key,editAmounts in yearSet.items.items.items():
					for editNumber in editNumbers:
						if editNumber not in editAmounts:
							continue
						fiscalYear,departmentCode,sectionCode,categoryCode,typeCode=key
						categoryName=yearSet.categories.names[categoryCode]
						categoryNameCodeAmounts[categoryName][categoryCode]+=editAmounts[editNumber]
						if categoryNameCodeAmounts[categoryName][categoryCode]==0:
							del categoryNameCodeAmounts[categoryName][categoryCode]
				categoryCodeset2=getCategoryCodeset()
				passiveCategoryCodeset2=collections.defaultdict(set)
				# update ids and codes
				for categoryName in sorted(categoryCodeset2.keys()):
					cs1=categoryCodeset1[categoryName]
					cs2=categoryCodeset2[categoryName]
					ps1=passiveCategoryCodeset1[categoryName]
					ps2=passiveCategoryCodeset2[categoryName]
					assert(not cs1&ps1)
					if len(cs1)==1 and len(cs2)==1 and cs1!=cs2:
						# code transfer case
						c1,=cs1
						c2,=cs2
						self.documentCodeIds[documentNumber2][c2]=self.documentCodeIds[documentNumber1][c1]
						# don't put c1 into passive codeset b/c it lost its id
						print('doc',documentNumber2,'reassign',c2,':=',c1,'cat',categoryName)
					else:
						# general case
						for c in cs1-cs2:
							ps2.add(c)
							self.documentCodeIds[documentNumber2][c]=self.documentCodeIds[documentNumber1][c]
							print('doc',documentNumber2,'deactivate',c,'cat',categoryName)
						for c in cs1&cs2:
							self.documentCodeIds[documentNumber2][c]=self.documentCodeIds[documentNumber1][c]
						for c in cs2-cs1-ps1:
							nIds+=1
							self.categoryIdNames[nIds]=categoryName
							self.documentCodeIds[documentNumber2][c]=nIds
							print('doc',documentNumber2,'new',c,'cat',categoryName)
						for c in cs2&ps1:
							self.documentCodeIds[documentNumber2][c]=self.documentCodeIds[documentNumber1][c]
							print('doc',documentNumber2,'reclaim',c,'cat',categoryName)
					for c in ps1-cs2:
						ps2.add(c)
						self.documentCodeIds[documentNumber2][c]=self.documentCodeIds[documentNumber1][c]
				documentNumber1=documentNumber2

	def getOrderedCategoryRows(self):
		for categoryId,categoryName in sorted(self.categoryIdNames.items()):
			yield {'categoryId':categoryId,'categoryName':categoryName}
	def getOrderedDocumentCategoryCodeRows(self):
		for documentNumber,codeIds in sorted(self.documentCodeIds.items()):
			for categoryCode,categoryId in sorted(codeIds.items()):
				yield {'documentNumber':documentNumber,'categoryId':categoryId,'categoryCode':categoryCode}
