#!/usr/bin/env python3

from decimal import Decimal
import sqlite3
import xlwt3 as xlwt

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
		outRow[-len(years)+years.index(row['year'])]=Decimal(row['amount'])/1000

# write xls
wb=xlwt.Workbook()
ws=wb.add_sheet('expenditures')
styleStandard=xlwt.easyxf('')
styleHeader=xlwt.easyxf('font: bold on; align: wrap on')
styleThinHeader=xlwt.easyxf('font: bold on, height 180; align: wrap on')
styleVeryThinHeader=xlwt.easyxf('font: height 140; align: wrap on')
styleAmount=xlwt.easyxf(num_format_str='#,##0.0')
nHeaderRows=1
ws.set_panes_frozen(True)
ws.set_horz_split_pos(nHeaderRows)
ws.row(nHeaderRows-1).height=1200
columns=[
	{'text':'Наименование',		'width':100,	'headerStyle':styleHeader,		'cellStyle':styleStandard},
	{'text':'Код ведомства',	'width':4,	'headerStyle':styleVeryThinHeader,	'cellStyle':styleStandard},
	{'text':'Код раздела',		'width':5,	'headerStyle':styleThinHeader,		'cellStyle':styleStandard},
	{'text':'Код целевой статьи',	'width':8,	'headerStyle':styleThinHeader,		'cellStyle':styleStandard},
	{'text':'Код вида расходов',	'width':4,	'headerStyle':styleVeryThinHeader,	'cellStyle':styleStandard},
]+[{'text':'Сумма на '+str(year)+' г. (тыс. руб.)','width':15,'headerStyle':styleHeader,'cellStyle':styleAmount} for year in years]
for nCol,col in enumerate(columns):
	ws.col(nCol).width=256*col['width']
	ws.write(nHeaderRows-1,nCol,col['text'],col['headerStyle'])
for nRow,row in enumerate(outRows):
	for nCol,(cell,col) in enumerate(zip(row,columns)):
		if cell is None:
			continue
		ws.write(nHeaderRows+nRow,nCol,cell,col['cellStyle'])
wb.save('out/pr03,04-2014-16.xls')
