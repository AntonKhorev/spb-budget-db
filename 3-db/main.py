#!/usr/bin/env python3

inputDirectory='../2-tables.out'
outputDirectory='../3-db.out'
outputFilename=outputDirectory+'/db.sql'
import os
if not os.path.exists(outputDirectory):
	os.makedirs(outputDirectory)

import glob
import csv
import decimal

import fileLists,dataLists

def readMetaTable(tableName,intColumns):
	def val(k,v):
		if v=='':
			return None
		elif k in intColumns:
			return int(v)
		else:
			return v
	csvFilename=inputDirectory+'/meta/'+tableName+'.csv'
	with open(csvFilename,encoding='utf8',newline='') as csvFile:
		return [{
			k:val(k,v) for k,v in row.items()
		} for row in csv.DictReader(csvFile)]

stages=readMetaTable('stages',{'stageYear','stageNumber'})
authors=readMetaTable('authors',{'authorId'})
documents=readMetaTable('documents',{'documentNumber','stageYear','stageNumber','amendmentFlag','authorId'})

edits=[]
departments=dataLists.DepartmentList()
superSections=dataLists.SuperSectionList()
sections=dataLists.SectionList()
categories=dataLists.CategoryList()
types=dataLists.TypeList()
items=dataLists.ItemList()

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

def getPriority(documentNumber):
	"priority to resolve name collisions for section/category/type codes"
	document=next(d for d in documents if d['documentNumber']==documentNumber)
	if document['amendmentFlag']==2:
		priority=300000 # law, published by fincom
	elif document['amendmentFlag']==0:
		priority=200000 # law project, published by fincom
	else:
		priority=100000 # amendment, published by assembly, often contains typos
	priority+=document['stageYear']*10
	priority+=document['stageNumber'] # prefer latter stage
	return priority

# scan section codes
for tableFile in fileLists.listTableFiles(glob.glob(inputDirectory+'/content/*.csv')):
	if tableFile.table!='section':
		continue
	priority=getPriority(tableFile.documentNumber)
	testOrder=makeTestOrder(['superSectionCode','sectionCode','categoryCode','typeCode'],[True,True,True,True])
	for row in readCsv(tableFile.filename):
		resets=testOrder(row)
		superSections.add(row,priority)
		sections.add(row,priority)
		categories.add(row,priority)
		types.add(row,priority)

# read monetary data
editNumber=0

# def makeUniqueCheck():
	# kv={}
	# def uniqueCheck(k,v):
		# if k in kv and kv[k]!=v:
			# print('@',k,':',kv[k],'vs',v)
		# kv[k]=v
	# return uniqueCheck
# uniqueCheck=makeUniqueCheck()

for tableFile in fileLists.listTableFiles(glob.glob(inputDirectory+'/content/*.csv')):
	if tableFile.table!='department':
		continue
	priority=getPriority(tableFile.documentNumber)
	editNumber+=1
	edits.append({
		'editNumber':editNumber,
		'documentNumber':tableFile.documentNumber,
		'paragraphNumber':tableFile.paragraphNumber,
	})
	if type(tableFile.action) is fileLists.SetAction:
		with items.makeSetContext(editNumber,tableFile.action.fiscalYears) as ctx:
			testOrder=makeTestOrder(['departmentCode','sectionCode','categoryCode','typeCode'],[False,True,True,True])
			for row in readCsv(tableFile.filename):
				resets=testOrder(row)
				if 'departmentCode' in resets:
					departments.resetSequence()
				departments.add(row,priority)
				categories.add(row,priority)
				types.add(row,priority)
				ctx.set(row)
				# uniqueCheck(row['categoryCode'],row['sectionCode'])
	elif type(tableFile.action) is fileLists.DiffsetAction:
		diffsetStartEditNumber=next(edit for edit in edits if edit['documentNumber']>tableFile.action.documentNumber)['editNumber']
		with items.makeDiffsetContext(editNumber,diffsetStartEditNumber,tableFile.action.fiscalYears) as ctx:
			testOrder=makeTestOrder(['departmentCode','sectionCode','categoryCode','typeCode'],[False,True,True,True])
			for row in readCsv(tableFile.filename):
				resets=testOrder(row)
				if 'departmentCode' in resets:
					departments.resetSequence()
				departments.add(row,priority)
				categories.add(row,priority)
				types.add(row,priority)
				ctx.set(row)
				# uniqueCheck(row['categoryCode'],row['sectionCode'])
	elif type(tableFile.action) is fileLists.DiffAction:
		for row in readCsv(tableFile.filename):
			departments.resetSequence() # ignore order
			departments.add(row,priority)
			categories.add(row,priority)
			types.add(row,priority)
			items.add(row,editNumber)
	elif type(tableFile.action) is fileLists.MoveAction:
		reader=readCsv(tableFile.filename)
		for s,t in zip(reader,reader):
			s['departmentCode']=departments.getCodeForName(s['departmentName'])
			del s['departmentName']
			t['departmentCode']=departments.getCodeForName(t['departmentName'])
			del t['departmentName']
			items.move(s,t,editNumber)
	else:
		raise Exception('unknown action '+str(tableFile.action))

### write sql ###

sql=open(outputFilename,'w',encoding='utf8')
sql.write("-- бюджет Санкт-Петербурга на 2014-2017 гг.\n")

def putValue(v):
	if type(v) is str:
		return "'"+v+"'"
	elif type(v) is int:
		return str(v)
	elif type(v) is decimal.Decimal:
		return str(int(v*1000))
	elif type(v) is bool:
		return str(int(v))
	elif v is None:
		return 'NULL'
	else:
		raise Exception('invalid type')
def putRowValues(row,cols):
	return ','.join(putValue(row[col]) for col in cols)
def writeTable(name,rows,cols):
	for row in rows:
		sql.write("INSERT INTO "+name+"("+','.join(cols)+") VALUES ("+putRowValues(row,cols)+");\n")

sql.write("""
CREATE TABLE stages(
	stageYear INT,
	stageNumber INT,
	stageAssemblyUrl TEXT,
	PRIMARY KEY (stageYear,stageNumber)
);
""");
writeTable('stages',stages,('stageYear','stageNumber','stageAssemblyUrl'))

sql.write("""
CREATE TABLE authors(
	authorId INT PRIMARY KEY,
	authorShortName TEXT,
	authorLongName TEXT
);
""");
writeTable('authors',authors,('authorId','authorShortName','authorLongName'))

sql.write("""
CREATE TABLE documents(
	documentNumber INT PRIMARY KEY,
	documentDate TEXT,
	stageYear INT,
	stageNumber INT,
	amendmentFlag INT,
	authorId INT,
	documentAssemblyUrl TEXT,
	FOREIGN KEY (stageYear,stageNumber) REFERENCES stages(stageYear,stageNumber),
	FOREIGN KEY (authorId) REFERENCES authors(authorId)
);
""");
writeTable('documents',documents,('documentNumber','documentDate','stageYear','stageNumber','amendmentFlag','authorId','documentAssemblyUrl'))

sql.write("""
CREATE TABLE edits(
	editNumber INT PRIMARY KEY,
	documentNumber INT,
	paragraphNumber TEXT,
	FOREIGN KEY (documentNumber) REFERENCES documents(documentNumber)
);
""");
writeTable('edits',edits,('editNumber','documentNumber','paragraphNumber'))

sql.write("""
CREATE TABLE departments(
	departmentCode CHAR(3) PRIMARY KEY,
	departmentName TEXT,
	departmentOrder INT
);
""")
writeTable('departments',departments.getOrderedRows(),('departmentCode','departmentName','departmentOrder'))

sql.write("""
CREATE TABLE superSections(
	superSectionCode CHAR(4) PRIMARY KEY,
	superSectionName TEXT
);
""")
writeTable('superSections',superSections.getOrderedRows(),('superSectionCode','superSectionName'))

sql.write("""
CREATE TABLE sections(
	sectionCode CHAR(4) PRIMARY KEY,
	superSectionCode CHAR(4),
	sectionName TEXT,
	FOREIGN KEY (superSectionCode) REFERENCES superSections(superSectionCode)
);
""")
writeTable('sections',sections.getOrderedRows(),('sectionCode','superSectionCode','sectionName'))

sql.write("""
CREATE TABLE categories(
	categoryCode CHAR(7) PRIMARY KEY,
	categoryName TEXT
);
""")
writeTable('categories',categories.getOrderedRows(),('categoryCode','categoryName'))

sql.write("""
CREATE TABLE types(
	typeCode CHAR(3) PRIMARY KEY,
	typeName TEXT
);
""")
writeTable('types',types.getOrderedRows(),('typeCode','typeName'))

sql.write("""
CREATE TABLE items(
	editNumber INT,
	fiscalYear INT,
	departmentCode CHAR(3),
	sectionCode CHAR(4),
	categoryCode CHAR(7),
	typeCode CHAR(3),
	amount INT,
	PRIMARY KEY (editNumber,fiscalYear,departmentCode,sectionCode,categoryCode,typeCode),
	FOREIGN KEY (editNumber) REFERENCES edits(editNumber),
	FOREIGN KEY (departmentCode) REFERENCES departments(departmentCode),
	FOREIGN KEY (sectionCode) REFERENCES sections(sectionCode),
	FOREIGN KEY (categoryCode) REFERENCES categories(categoryCode),
	FOREIGN KEY (typeCode) REFERENCES types(typeCode)
);
"""); # amount DECIMAL(10,1) - but sqlite doesn't support decimal
writeTable('items',items.getOrderedRows(),('editNumber','fiscalYear','departmentCode','sectionCode','categoryCode','typeCode','amount'))
