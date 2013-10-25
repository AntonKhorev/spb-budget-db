#!/usr/bin/env python3

import sqlite3

levelColLists=[
	['departmentCode'],
	['sectionCode','categoryCode'],
	['typeCode'],
]
levelNames=[
	'departmentName',
	'categoryName',
	'typeName',
]
years=[2014,2015,2016]

def outputLevel(row,level):
	line=[]
	line.append(row[levelNames[level]])
	for l,levelColList in enumerate(levelColLists):
		for levelCol in levelColList:
			if l<=level:
				line.append(row[levelCol])
			else:
				line.append(None)
	if level==len(levelColLists)-1:
		line.append(row['amount'])
	else:
		line.append(None)
	return line

with sqlite3.connect(':memory:') as conn:
	conn.row_factory=sqlite3.Row
	conn.execute('pragma foreign_keys=ON')
	conn.executescript(
		open('db/pr-bd-2014-16.sql',encoding='utf8').read()
	)
	insides=[None]*len(levelColLists)
	for row in conn.execute("""
		SELECT departmentName,categoryName,typeName,departmentCode,sectionCode,categoryCode,typeCode,year,amount
		FROM items
		JOIN departments USING(departmentCode)
		JOIN categories USING(categoryCode)
		JOIN types USING(typeCode)
		WHERE year=2014
		ORDER BY departmentOrder,sectionCode,categoryCode,typeCode,year
	"""):
		newInsides=False
		for level,levelColList in enumerate(levelColLists):
			nextInside=tuple(row[col] for col in levelColList)
			if newInsides or insides[level]!=nextInside:
				print(outputLevel(row,level))
				insides[level]=nextInside
				newInsides=True
