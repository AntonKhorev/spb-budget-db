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

class CategoryList:
	def __init__(self):
		self.names={}
		self.prevRow=None
	def resetSequence(self):
		self.prevRow=None
	def add(self,row):
		code=row['categoryCode']
		name=row['categoryName']
		if code in self.names:
			if self.names[code]!=name:
				raise Exception('code collision: categories['+code+'] = '+str(self.names[code])+' vs '+str(names))
		else:
			self.names[code]=name
		if self.prevRow is not None and self.prevRow['departmentCode']==row['departmentCode']:
			if (self.prevRow['sectionCode'],self.prevRow['categoryCode'])>(row['sectionCode'],row['categoryCode']):
				raise Exception('invalid category order')
	def getOrderedRows(self):
		for code,name in sorted(self.names.items()):
			yield {'categoryCode':code,'categoryName':name}

departments=DepartmentList()
categories=CategoryList()

for csvFilename in ('tables/pr03-2014-16.csv','tables/pr04-2014-16.csv'):
	departments.resetSequence()
	categories.resetSequence()
	with open(csvFilename,encoding='utf8',newline='') as csvFile:
		cols=None
		for row in csv.DictReader(csvFile):
			if row['departmentCode']:
				departments.add(row['departmentCode'],row['departmentName'])
			if row['categoryCode']:
				categories.add(row)

sql=open('db/pr-bd-2014-16.sql','w',encoding='utf8')

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
