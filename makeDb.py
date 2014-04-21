#!/usr/bin/env python3

import itertools
import glob
import csv
import decimal

import fileLists,dataLists

documents=[
	{'documentNumber':3574,'documentDate':'2013-10-07','governorFlag':True,'amendmentFlag':False},
	{'documentNumber':3765,'documentDate':'2013-11-01','governorFlag':True,'amendmentFlag':True},
	{'documentNumber':3781,'documentDate':'2013-11-08','governorFlag':False,'amendmentFlag':True},
	{'documentNumber':3850,'documentDate':'2013-11-15','governorFlag':False,'amendmentFlag':True},
	{'documentNumber':4597,'documentDate':'2014-04-11','governorFlag':True,'amendmentFlag':False},
]
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
			if 'year' in row:
				row['year']=int(row['year'])
			yield row

# scan section codes
for tableFile in fileLists.listTableFiles(glob.glob('tables/*.csv')):
	if tableFile.table!='section':
		continue
	if tableFile.stage=='2014.0.z':
		priority=1
	else:
		priority=2
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

for tableFile in fileLists.listTableFiles(glob.glob('tables/*.csv')):
	if tableFile.table!='department':
		continue
	if tableFile.stage=='2014.0.z':
		priority=1
	elif tableFile.documentNumber==3574:
		priority=2
	else:
		priority=3
	editNumber+=1
	edits.append({
		'editNumber':editNumber,
		'documentNumber':tableFile.documentNumber,
		'paragraphNumber':tableFile.paragraphNumber,
	})
	if type(tableFile.action) is fileLists.SetAction:
		with items.makeSetContext(editNumber,tableFile.action.years) as setContext:
			testOrder=makeTestOrder(['departmentCode','sectionCode','categoryCode','typeCode'],[False,True,True,True])
			for row in readCsv(tableFile.filename):
				resets=testOrder(row)
				if 'departmentCode' in resets:
					departments.resetSequence()
				departments.add(row,priority)
				categories.add(row,priority)
				types.add(row,priority)
				setContext.set(row)
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

sql=open('db/pr-bd-2014-16.sql','w',encoding='utf8')
sql.write("-- проект бюджета Санкт-Петербурга на 2014-2016 гг.\n")

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
CREATE TABLE documents(
	documentNumber INT PRIMARY KEY,
	documentDate TEXT,
	governorFlag INT(1),
	amendmentFlag INT(1)
);
""");
writeTable('documents',documents,('documentNumber','documentDate','governorFlag','amendmentFlag'))

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
	year INT,
	departmentCode CHAR(3),
	sectionCode CHAR(4),
	categoryCode CHAR(7),
	typeCode CHAR(3),
	amount INT,
	PRIMARY KEY (editNumber,year,departmentCode,sectionCode,categoryCode,typeCode),
	FOREIGN KEY (editNumber) REFERENCES edits(editNumber),
	FOREIGN KEY (departmentCode) REFERENCES departments(departmentCode),
	FOREIGN KEY (sectionCode) REFERENCES sections(sectionCode),
	FOREIGN KEY (categoryCode) REFERENCES categories(categoryCode),
	FOREIGN KEY (typeCode) REFERENCES types(typeCode)
);
"""); # amount DECIMAL(10,1) - but sqlite doesn't support decimal
writeTable('items',items.getOrderedRows(),('editNumber','year','departmentCode','sectionCode','categoryCode','typeCode','amount'))
