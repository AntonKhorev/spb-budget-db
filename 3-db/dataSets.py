import glob,csv
import fileLists,dataLists

class YearSet:
	def __init__(self,stageYear,inputDirectory,getDocumentPriority):
		self.stageYear=stageYear
		self.edits=[]
		self.departments=dataLists.DepartmentList()
		self.superSections=dataLists.SuperSectionList()
		self.sections=dataLists.SectionList()
		self.categories=dataLists.CategoryList()
		self.types=dataLists.TypeList()
		self.items=dataLists.ItemList()

		def makeTestOrder(cols,stricts):
			prevs=[None]*len(cols)
			def testOrder(row):
				resets=set()
				resetFlag=False
				for col,strict,prev in zip(cols,stricts,prevs):
					if resetFlag:
						resets.add(col)
						continue
					if not prev:
						resetFlag=True
						resets.add(col)
						continue
					if strict and row[col]<prev:
						raise Exception('invalid order for '+col)
					if row[col]!=prev:
						resetFlag=True
				for i,col in enumerate(cols):
					prevs[i]=row[col]
				return resets
			return testOrder

		def readCsv(csvFilename):
			with open(csvFilename,encoding='utf8',newline='') as csvFile:
				for row in csv.DictReader(csvFile):
					if 'fiscalYear' in row:
						row['fiscalYear']=int(row['fiscalYear'])
					yield row

		# scan section codes
		print('==',stageYear,'scan section codes ==')
		for tableFile in fileLists.listTableFiles(glob.glob(inputDirectory+'/content/'+str(stageYear)+'.*.csv')):
			if tableFile.table!='section':
				continue
			priority=getDocumentPriority(tableFile.documentNumber)
			testOrder=makeTestOrder(['superSectionCode','sectionCode','categoryCode','typeCode'],[True,True,True,True])
			for row in readCsv(tableFile.filename):
				resets=testOrder(row)
				self.superSections.add(row,priority)
				self.sections.add(row,priority)
				self.categories.add(row,priority)
				self.types.add(row,priority)

		# read monetary data
		print('==',stageYear,'read monetary data ==')
		editNumber=0
		for tableFile in fileLists.listTableFiles(glob.glob(inputDirectory+'/content/'+str(stageYear)+'.*.csv')):
			if tableFile.table!='department':
				continue
			priority=getDocumentPriority(tableFile.documentNumber)
			editNumber+=1
			self.edits.append({
				'editNumber':editNumber,
				'documentNumber':tableFile.documentNumber,
				'paragraphNumber':tableFile.paragraphNumber,
			})
			if type(tableFile.action) is fileLists.SetAction:
				with self.items.makeSetContext(editNumber,tableFile.action.fiscalYears) as ctx:
					testOrder=makeTestOrder(['departmentCode','sectionCode','categoryCode','typeCode'],[False,True,True,True])
					for row in readCsv(tableFile.filename):
						resets=testOrder(row)
						if 'departmentCode' in resets:
							self.departments.resetSequence()
						self.departments.add(row,priority)
						self.categories.add(row,priority)
						self.types.add(row,priority)
						ctx.set(row)
			elif type(tableFile.action) is fileLists.DiffsetAction:
				diffsetStartEditNumber=next(edit for edit in self.edits if edit['documentNumber']>tableFile.action.documentNumber)['editNumber']
				with self.items.makeDiffsetContext(editNumber,diffsetStartEditNumber,tableFile.action.fiscalYears) as ctx:
					testOrder=makeTestOrder(['departmentCode','sectionCode','categoryCode','typeCode'],[False,True,True,True])
					for row in readCsv(tableFile.filename):
						resets=testOrder(row)
						if 'departmentCode' in resets:
							self.departments.resetSequence()
						self.departments.add(row,priority)
						self.categories.add(row,priority)
						self.types.add(row,priority)
						ctx.set(row)
			elif type(tableFile.action) is fileLists.DiffAction:
				for row in readCsv(tableFile.filename):
					self.departments.resetSequence() # ignore order
					self.departments.add(row,priority)
					self.categories.add(row,priority)
					self.types.add(row,priority)
					self.items.add(row,editNumber)
			elif type(tableFile.action) is fileLists.MoveAction:
				reader=readCsv(tableFile.filename)
				for s,t in zip(reader,reader):
					s['departmentCode']=self.departments.getCodeForName(s['departmentName'])
					del s['departmentName']
					t['departmentCode']=self.departments.getCodeForName(t['departmentName'])
					del t['departmentName']
					self.items.move(s,t,editNumber)
			else:
				raise Exception('unknown action '+str(tableFile.action))

class InterYearSet:
	def __init__(self,yearSets):
		print('== merge years ==')
		self.departments=dataLists.DepartmentList()
		self.superSections=dataLists.SuperSectionList()
		self.sections=dataLists.SectionList()
		self.types=dataLists.TypeList()
		for yearSet in yearSets:
			priority=yearSet.stageYear
			self.departments.resetSequence()
			for row in yearSet.departments.getOrderedRows():
				self.departments.add(row,priority)
			for row in yearSet.superSections.getOrderedRows():
				self.superSections.add(row,priority)
			for row in yearSet.sections.getOrderedRows():
				self.sections.add(row,priority)
			for row in yearSet.types.getOrderedRows():
				self.types.add(row,priority)
		self.categories=dataLists.InterYearCategoryList(yearSets)
		# self.edits=[]
		# self.items=dataLists.ItemList()
