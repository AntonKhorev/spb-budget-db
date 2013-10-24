#!/usr/bin/env python3

import decimal
import re
import csv
from openpyxl import load_workbook

def convertXslxToCsv(inputFilename,outputFilename,years):
	wb=load_workbook(inputFilename)
	ws=wb.get_active_sheet()
	maxRow=ws.get_highest_row()

	for nRow in range(maxRow):
		if ws.cell(row=nRow,column=0).value==1:
			break
	else:
		raise Exception('table start not found')

	rows=[{}]*len(years) # reserve first rows for totals
	departmentNameRe=re.compile(r'(?P<departmentName>.*?)\s*\((?P<departmentCode>...)\)')

	for nRow in range(nRow,maxRow):
		def makeDecimalAmount(amount):
			if type(amount) is int:
				amount=str(amount)+'.0'
			else:
				amount=str(amount)
			return decimal.Decimal(amount)
		number,name,sectionCode,categoryCode,typeCode=(ws.cell(row=nRow,column=c).value for c in range(5))
		name=' '.join(name.split())
		amounts=[makeDecimalAmount(ws.cell(row=nRow,column=c).value) for c in range(5,5+len(years))]
		sectionCode=sectionCode[:2]+sectionCode[-2:]
		typeCode=str(typeCode)
		amountCol=None
		row={}
		addRow=rows.append
		if not number:
			def makeAddRow():
				nRow=0
				def addRow(row):
					nonlocal nRow,rows
					rows[nRow]=row
					nRow+=1
				return addRow
			addRow=makeAddRow()
			amountCol='yAmount'
		elif not sectionCode:
			m=departmentNameRe.match(name)
			row['departmentName']=departmentName=m.group('departmentName')
			row['departmentCode']=departmentCode=m.group('departmentCode')
			amountCol='ydAmount'
		elif not typeCode:
			row['departmentName']=departmentName
			row['departmentCode']=departmentCode
			row['sectionCode']=sectionCode
			row['categoryName']=categoryName=name
			row['categoryCode']=categoryCode
			amountCol='ydscAmount'
		else:
			row['departmentName']=departmentName
			row['departmentCode']=departmentCode
			row['sectionCode']=sectionCode
			row['categoryName']=categoryName
			row['categoryCode']=categoryCode
			row['typeName']=typeName=name
			row['typeCode']=typeCode
			amountCol='ydsctAmount'
		for year,amount in zip(years,amounts):
			r=row.copy()
			r['year']=year
			r[amountCol]=amount
			addRow(r)
		if not number:
			break
	else:
		raise Exception('no total line found')

	writer=csv.writer(open(outputFilename,'w',newline='',encoding='utf8'),quoting=csv.QUOTE_NONNUMERIC)
	cols=[
		'year',
		'departmentName','departmentCode',
		'sectionCode','categoryName','categoryCode',
		'typeName','typeCode',
		'yAmount','ydAmount','ydscAmount','ydsctAmount',
	]
	writer.writerow(cols)
	for row in rows:
		writer.writerow([row.get(col) for col in cols])

convertXslxToCsv('fincom/pr03-2014-16.xlsx','tables/pr03-2014-16.csv',[2014])
convertXslxToCsv('fincom/pr04-2014-16.xlsx','tables/pr04-2014-16.csv',[2015,2016])
