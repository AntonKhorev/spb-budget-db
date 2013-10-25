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

def outputLevelRow(row,level):
	outRow=[]
	outRow.append(row[levelNames[level]])
	for l,levelColList in enumerate(levelColLists):
		for levelCol in levelColList:
			if l<=level:
				outRow.append(row[levelCol])
			else:
				outRow.append(None)
	outRow+=[None]*len(years)
	return outRow

outRows=[]

with sqlite3.connect(':memory:') as conn:
	conn.row_factory=sqlite3.Row
	conn.execute('pragma foreign_keys=ON')
	conn.executescript(
		open('db/pr-bd-2014-16.sql',encoding='utf8').read()
	)
	outRow=None
	insides=[None]*len(levelColLists)
	for row in conn.execute("""
		SELECT departmentName,categoryName,typeName,departmentCode,sectionCode,categoryCode,typeCode,year,amount
		FROM items
		JOIN departments USING(departmentCode)
		JOIN categories USING(categoryCode)
		JOIN types USING(typeCode)
		ORDER BY departmentOrder,sectionCode,categoryCode,typeCode,year
	"""):
		# TODO filter years
		newInsides=False
		for level,levelColList in enumerate(levelColLists):
			nextInside=tuple(row[col] for col in levelColList)
			if newInsides or insides[level]!=nextInside:
				outRow=outputLevelRow(row,level)
				outRows.append(outRow)
				insides[level]=nextInside
				newInsides=True
		outRow[-len(years)+years.index(row['year'])]=row['amount']

for outRow in outRows:
	print(outRow)
