#!/usr/bin/env python3

inputDirectory='../2-tables.out'
outputDirectory='../3-db.out'
outputFilename=outputDirectory+'/db.sql'
import os
if not os.path.exists(outputDirectory):
	os.makedirs(outputDirectory)

import csv,decimal
import dataSets

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

# TODO replace w/ priorities derived from source types
def getDocumentPriority(documentNumber):
	"priority to resolve name collisions for section/category/type codes"
	document=next(d for d in documents if d['documentNumber']==documentNumber)
	if document['amendmentFlag']==2:
		priority=30 # law, published by fincom
	elif document['amendmentFlag']==0:
		priority=20 # law project, published by fincom
	else:
		priority=10 # amendment, published by assembly, often contains typos
	priority+=document['stageNumber'] # prefer latter stage
	return priority

ys2014=dataSets.YearSet(2014,inputDirectory,getDocumentPriority)
ys2015=dataSets.YearSet(2015,inputDirectory,getDocumentPriority)
iys=dataSets.InterYearSet([ys2014,ys2015])

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
writeTable('edits',iys.edits,('editNumber','documentNumber','paragraphNumber'))

sql.write("""
CREATE TABLE departments(
	departmentCode CHAR(3) PRIMARY KEY,
	departmentName TEXT,
	departmentOrder INT
);
""")
writeTable('departments',iys.departments.getOrderedRows(),('departmentCode','departmentName','departmentOrder'))

sql.write("""
CREATE TABLE superSections(
	superSectionCode CHAR(4) PRIMARY KEY,
	superSectionName TEXT
);
""")
writeTable('superSections',iys.superSections.getOrderedRows(),('superSectionCode','superSectionName'))

sql.write("""
CREATE TABLE sections(
	sectionCode CHAR(4) PRIMARY KEY,
	superSectionCode CHAR(4),
	sectionName TEXT,
	FOREIGN KEY (superSectionCode) REFERENCES superSections(superSectionCode)
);
""")
writeTable('sections',iys.sections.getOrderedRows(),('sectionCode','superSectionCode','sectionName'))

sql.write("""
CREATE TABLE categories(
	categoryId INT PRIMARY KEY,
	categoryName TEXT
);
""")
writeTable('categories',iys.categories.getOrderedCategoryRows(),('categoryId','categoryName'))

sql.write("""
CREATE TABLE documentCategoryCodes(
	documentNumber INT, -- usually filtered first by document
	categoryId INT,
	categoryCode CHAR(7),
	PRIMARY KEY (documentNumber,categoryId),
	FOREIGN KEY (documentNumber) REFERENCES documents(documentNumber),
	FOREIGN KEY (categoryId) REFERENCES categories(categoryId)
);
""")
writeTable('categories',iys.categories.getOrderedDocumentCategoryCodeRows(),('documentNumber','categoryId','categoryCode'))

sql.write("""
CREATE TABLE types(
	typeCode CHAR(3) PRIMARY KEY,
	typeName TEXT
);
""")
writeTable('types',iys.types.getOrderedRows(),('typeCode','typeName'))

sql.write("""
CREATE TABLE items(
	editNumber INT,
	fiscalYear INT,
	departmentCode CHAR(3),
	sectionCode CHAR(4),
	categoryId INT,
	typeCode CHAR(3),
	amount INT, -- in roubles, not in thousands
	PRIMARY KEY (editNumber,fiscalYear,departmentCode,sectionCode,categoryCode,typeCode),
	FOREIGN KEY (editNumber) REFERENCES edits(editNumber),
	FOREIGN KEY (departmentCode) REFERENCES departments(departmentCode),
	FOREIGN KEY (sectionCode) REFERENCES sections(sectionCode),
	FOREIGN KEY (categoryId) REFERENCES categories(categoryId),
	FOREIGN KEY (typeCode) REFERENCES types(typeCode)
);
"""); # amount DECIMAL(10,1) - but sqlite doesn't support decimal
writeTable('items',iys.items.getOrderedRows(),('editNumber','fiscalYear','departmentCode','sectionCode','categoryId','typeCode','amount'))
