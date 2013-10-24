#!/usr/bin/env python3

import csv
import collections

class DepartmentList:
	def __init__(self):
		self.names={}
		self.vertices=collections.defaultdict(set)
		self.prevCode=None
	def resetSequence(self):
		self.prevCode=None
	def add(self,code,name):
		if code in self.names:
			if self.names[code]!=name:
				raise Exception('code collision: departments['+str(code)+'] = '+str(self.names[code])+' vs '+str(name))
		else:
			self.names[code]=name
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

class AbstractList:
	def __init__(self):
		self.names={}
	def add(self,row):
		code=row[self.codeCol]
		name=row[self.nameCol]
		if code in self.names:
			if self.names[code]!=name:
				raise Exception('code collision: '+self.codeCol+' = '+code+'; '+self.nameCol+' = '+str(self.names[code])+' vs '+str(names))
		else:
			self.names[code]=name
	def getOrderedRows(self):
		for code,name in sorted(self.names.items()):
			yield {self.codeCol:code,self.nameCol:name}

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

departments=DepartmentList()
categories=CategoryList()
types=TypeList()
items=[]

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

for csvFilename in ('tables/pr03-2014-16.csv','tables/pr04-2014-16.csv'):
	testOrder=makeTestOrder(['departmentCode','sectionCode','categoryCode','typeCode'],[False,True,True,True])
	with open(csvFilename,encoding='utf8',newline='') as csvFile:
		for row in csv.DictReader(csvFile):
			resets=testOrder(row)
			if 'departmentCode' in resets:
				departments.resetSequence()
			if row['departmentCode']:
				departments.add(row['departmentCode'],row['departmentName'])
			if row['categoryCode']:
				categories.add(row)
			if row['typeCode']:
				types.add(row)
				if row['ydsctAmount']!='0.0':
					items.append(row)

sql=open('db/pr-bd-2014-16.sql','w',encoding='utf8')
sql.write("-- проект бюджета Санкт-Петербурга на 2014-2016 гг.\n")

sql.write("""
CREATE TABLE departments(
	departmentCode CHAR(3) PRIMARY KEY,
	departmentName TEXT,
	departmentOrder INT
);
""")
for row in departments.getOrderedRows():
	sql.write("INSERT INTO departments(departmentCode,departmentName,departmentOrder) VALUES ('"+row['departmentCode']+"','"+row['departmentName']+"',"+str(row['departmentOrder'])+");\n")

sql.write("""
CREATE TABLE categories(
	categoryCode CHAR(7) PRIMARY KEY,
	categoryName TEXT
);
""")
for row in categories.getOrderedRows():
	sql.write("INSERT INTO categories(categoryCode,categoryName) VALUES ('"+row['categoryCode']+"','"+row['categoryName']+"');\n")

sql.write("""
CREATE TABLE types(
	typeCode CHAR(3) PRIMARY KEY,
	typeName TEXT
);
""")
for row in types.getOrderedRows():
	sql.write("INSERT INTO types(typeCode,typeName) VALUES ('"+row['typeCode']+"','"+row['typeName']+"');\n")

def amount(amount):
	if amount[-2]!='.':
		raise Exception('invalid amount '+amount)
	return str(int(amount[:-2]+amount[-1]+'00'))
sql.write("""
CREATE TABLE items(
	year INT,
	departmentCode CHAR(3),
	sectionCode CHAR(4),
	categoryCode CHAR(7),
	typeCode CHAR(3),
	amount INT,
	PRIMARY KEY (year,departmentCode,sectionCode,categoryCode,typeCode),
	FOREIGN KEY (departmentCode) REFERENCES departments(departmentCode),
	FOREIGN KEY (categoryCode) REFERENCES categories(categoryCode),
	FOREIGN KEY (typeCode) REFERENCES types(typeCode)
);
"""); # amount DECIMAL(10,1) - but sqlite doesn't support decimal
for row in sorted(items,key=lambda r: (r['year'],r['departmentCode'],r['sectionCode'],r['categoryCode'],r['typeCode'])):
	sql.write(
		"INSERT INTO items(year,departmentCode,sectionCode,categoryCode,typeCode,amount) VALUES ("+
		row['year']+",'"+row['departmentCode']+"','"+row['sectionCode']+"','"+row['categoryCode']+"','"+row['typeCode']+"',"+amount(row['ydsctAmount'])+
		");\n"
	)
