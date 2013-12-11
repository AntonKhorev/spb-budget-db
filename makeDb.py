#!/usr/bin/env python3

import decimal
import itertools,collections
import re,glob
import csv
import dataLists

def listDocumentParagraphs(csvFilenameGlob):
	r=re.compile(r'^.+[/\\]\d+\.\d\.[pz]\.(?P<number>\d[0-9.]+)\.(?P<table>[a-z]+)\.csv$')
	def parse(csvFilename):
		m=r.match(csvFilename)
		if not m: raise Exception('invalid filename '+str(csvFilename))
		sortKey=tuple(int(n) for n in m.group('number').split('.'))
		return sortKey,m.group('table'),csvFilename
	return itertools.groupby(((numbers[0],'.'.join(str(n) for n in numbers[1:]),table,csvFilename) for numbers,table,csvFilename in sorted(
		parse(csvFilename) for csvFilename in glob.glob(csvFilenameGlob)
	)), lambda t:t[0])

documents=[
	{'documentNumber':3574,'documentDate':'2013-10-07','governorFlag':True,'amendmentFlag':False},
	{'documentNumber':3765,'documentDate':'2013-11-01','governorFlag':True,'amendmentFlag':True},
	{'documentNumber':3781,'documentDate':'2013-11-08','governorFlag':False,'amendmentFlag':True},
]
edits=[]
departments=dataLists.DepartmentList()
superSections=dataLists.SuperSectionList()
sections=dataLists.SectionList()
categories=dataLists.CategoryList()
types=dataLists.TypeList()
items=[]

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
		itemSums[self.keyToTuple(row)]+=decimal.Decimal(row['ydsscctAmount'])
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
itemSums=ItemSums()

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

# scan section codes
for csvFilenamePrefix in ('tables/2014.0.p.','tables/2014.0.z.'):
	for documentNumber,paragraphs in listDocumentParagraphs(csvFilenamePrefix+'*.section.csv'):
		for documentNumber,paragraphNumber,table,csvFilename in paragraphs:
			testOrder=makeTestOrder(['superSectionCode','sectionCode','categoryCode','typeCode'],[True,True,True,True])
			with open(csvFilename,encoding='utf8',newline='') as csvFile:
				for row in csv.DictReader(csvFile):
					resets=testOrder(row)
					if row['superSectionCode']:
						superSections.add(row)
					if row['sectionCode']:
						sections.add(row)
					if row['categoryCode']:
						categories.add(row)
					if row['typeCode']:
						types.add(row)

# read monetary data
amendmentFlag=False
editNumber=0
for documentNumber,paragraphs in listDocumentParagraphs('tables/2014.0.p.*.csv'):
	for documentNumber,paragraphNumber,table,csvFilename in paragraphs:
		if table not in ('department','move'): continue
		editNumber+=1
		edits.append({
			'editNumber':editNumber,
			'documentNumber':documentNumber,
			'paragraphNumber':paragraphNumber,
		})
		if table=='department':
			if not amendmentFlag:
				testOrder=makeTestOrder(['departmentCode','sectionCode','categoryCode','typeCode'],[False,True,True,True])
			with open(csvFilename,encoding='utf8',newline='') as csvFile:
				for row in csv.DictReader(csvFile):
					if not amendmentFlag:
						resets=testOrder(row)
						if 'departmentCode' in resets:
							departments.resetSequence()
					if row['departmentCode']:
						if amendmentFlag:
							departments.resetSequence() # ignore order
						departments.add(row)
					if row['categoryCode']:
						categories.add(row)
					if row['typeCode']:
						types.add(row)
						if row['ydsscctAmount']!='0.0':
							row['editNumber']=editNumber
							items.append(row)
							itemSums.add(row)
		elif table=='move':
			with open(csvFilename,encoding='utf8',newline='') as csvFile:
				reader=csv.DictReader(csvFile)
				for s,t in zip(reader,reader):
					s['departmentCode']=departments.getCodeForName(s['departmentName'])
					del s['departmentName']
					t['departmentCode']=departments.getCodeForName(t['departmentName'])
					del t['departmentName']
					for row in itemSums.makeMoveItems(s,t):
						row['editNumber']=editNumber
						items.append(row)
	amendmentFlag=True

# def makeUniqueCheck():
	# kv={}
	# def uniqueCheck(k,v):
		# if k in kv and kv[k]!=v:
			# print('@',k,':',kv[k],'vs',v)
		# kv[k]=v
	# return uniqueCheck

# compare with the law
# uniqueCheck=makeUniqueCheck()
for documentNumber,paragraphs in listDocumentParagraphs('tables/2014.0.z.*.department.csv'):
	for documentNumber,paragraphNumber,table,csvFilename in paragraphs:
		testOrder=makeTestOrder(['departmentCode','sectionCode','categoryCode','typeCode'],[False,True,True,True])
		with open(csvFilename,encoding='utf8',newline='') as csvFile:
			for row in csv.DictReader(csvFile):
				resets=testOrder(row)
				if 'departmentCode' in resets:
					departments.resetSequence()
				if row['departmentCode']:
					departments.add(row)
				if row['categoryCode']:
					categories.add(row)
				if row['typeCode']:
					types.add(row)
					if row['ydsscctAmount']!='0.0':
						itemSums.fix(row)
					# uniqueCheck(row['categoryCode'],row['sectionCode'])
for key in sorted(itemSums):
	if itemSums[key]:
		print('* unknown amendment:',key,itemSums[key])

### write sql ###

sql=open('db/pr-bd-2014-16.sql','w',encoding='utf8')
sql.write("-- проект бюджета Санкт-Петербурга на 2014-2016 гг.\n")

sql.write("""
CREATE TABLE documents(
	documentNumber INT PRIMARY KEY,
	documentDate TEXT,
	governorFlag INT(1),
	amendmentFlag INT(1)
);
""");
for row in documents:
	sql.write(
		"INSERT INTO documents(documentNumber,documentDate,governorFlag,amendmentFlag) VALUES ("+
		str(row['documentNumber'])+",'"+row['documentDate']+"',"+str(int(row['governorFlag']))+","+str(int(row['amendmentFlag']))+");\n"
	)

sql.write("""
CREATE TABLE edits(
	editNumber INT PRIMARY KEY,
	documentNumber INT,
	paragraphNumber TEXT,
	FOREIGN KEY (documentNumber) REFERENCES documents(documentNumber)
);
""");
for row in edits:
	sql.write(
		"INSERT INTO edits(editNumber,documentNumber,paragraphNumber) VALUES ("+
		str(row['editNumber'])+","+str(row['documentNumber'])+",'"+row['paragraphNumber']+"');\n"
	)

sql.write("""
CREATE TABLE departments(
	departmentCode CHAR(3) PRIMARY KEY,
	departmentName TEXT,
	departmentOrder INT
);
""")
for row in departments.getOrderedRows():
	sql.write(
		"INSERT INTO departments(departmentCode,departmentName,departmentOrder) VALUES ('"+
		row['departmentCode']+"','"+row['departmentName']+"',"+str(row['departmentOrder'])+");\n"
	)

sql.write("""
CREATE TABLE superSections(
	superSectionCode CHAR(4) PRIMARY KEY,
	superSectionName TEXT
);
""")
for row in superSections.getOrderedRows():
	sql.write(
		"INSERT INTO superSections(superSectionCode,superSectionName) VALUES ('"+
		row['superSectionCode']+"','"+row['superSectionName']+"');\n"
	)

sql.write("""
CREATE TABLE sections(
	sectionCode CHAR(4) PRIMARY KEY,
	superSectionCode CHAR(4),
	sectionName TEXT,
	FOREIGN KEY (superSectionCode) REFERENCES superSections(superSectionCode)
);
""")
for row in sections.getOrderedRows():
	sql.write(
		"INSERT INTO sections(sectionCode,superSectionCode,sectionName) VALUES ('"+
		row['sectionCode']+"','"+row['superSectionCode']+"','"+row['sectionName']+"');\n"
	)

sql.write("""
CREATE TABLE categories(
	categoryCode CHAR(7) PRIMARY KEY,
	categoryName TEXT
);
""")
for row in categories.getOrderedRows():
	sql.write(
		"INSERT INTO categories(categoryCode,categoryName) VALUES ('"+
		row['categoryCode']+"','"+row['categoryName']+"');\n"
	)

sql.write("""
CREATE TABLE types(
	typeCode CHAR(3) PRIMARY KEY,
	typeName TEXT
);
""")
for row in types.getOrderedRows():
	sql.write(
		"INSERT INTO types(typeCode,typeName) VALUES ('"+
		row['typeCode']+"','"+row['typeName']+"');\n"
	)

def amount(amount):
	amount=str(amount)
	if amount[-2]!='.':
		raise Exception('invalid amount '+amount)
	return str(int(amount[:-2]+amount[-1]+'00'))
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
for row in sorted(items,key=lambda r: (int(r['editNumber']),r['year'],r['departmentCode'],r['sectionCode'],r['categoryCode'],r['typeCode'])):
	sql.write(
		"INSERT INTO items(editNumber,year,departmentCode,sectionCode,categoryCode,typeCode,amount) VALUES ("+
		str(row['editNumber'])+","+row['year']+",'"+row['departmentCode']+"','"+row['sectionCode']+"','"+row['categoryCode']+"','"+row['typeCode']+"',"+amount(row['ydsscctAmount'])+
		");\n"
	)
