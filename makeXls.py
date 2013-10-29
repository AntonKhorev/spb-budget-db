#!/usr/bin/env python3

from decimal import Decimal
import sqlite3

import xlwt3 as xlwt
# import xlsxwriter

class LevelTable:
	def __init__(self,levelColLists,levelNames,years,rows,nHeaderRows=2):
		self.levelColLists=levelColLists
		self.years=years
		self.nHeaderRows=nHeaderRows

		self.outRows=[['Итого']+[None for levelColList in self.levelColLists for col in levelColList]+[None]*len(self.years)]
		self.levels=[0]
		def outputLevelRow(row,level):
			outRow=[]
			outRow.append(row[levelNames[level]])
			for l,levelColList in enumerate(self.levelColLists):
				for levelCol in levelColList:
					if l<=level:
						outRow.append(row[levelCol])
					else:
						outRow.append(None)
			outRow+=[None]*len(self.years)
			return outRow

		nLevels=len(self.levelColLists)
		outRow=None
		insides=[None]*nLevels
		summands=[[]]+[None]*nLevels
		sums=[0]+[None]*nLevels
		def clearSumsForLevel(level):
			if level<nLevels and summands[level+1]:
				nFirstAmountCol=len(self.outRows[0])-len(self.years)
				for y in range(len(self.years)):
					colChar=chr(ord('A')+nFirstAmountCol+y)
					self.outRows[sums[level+1]][nFirstAmountCol+y]='='+'+'.join(
						colChar+str(1+self.nHeaderRows+summand) for summand in summands[level+1]
					) # TODO SUBTOTAL()

		nRow=0
		for row in rows:
			clear=False
			for level,levelColList in enumerate(self.levelColLists):
				nextInside=tuple(row[col] for col in levelColList)
				if clear or insides[level]!=nextInside:
					nRow+=1
					clearSumsForLevel(level)
					summands[level+1]=[]
					sums[level+1]=nRow
					summands[level].append(nRow)
					outRow=outputLevelRow(row,level)
					self.outRows.append(outRow)
					self.levels.append(level)
					insides[level]=nextInside
					clear=True
			outRow[-len(self.years)+self.years.index(row['year'])]=Decimal(row['amount'])/1000
		for level in range(-1,nLevels):
			clearSumsForLevel(level)

	def makeXls(self,tableTitle,outputFilename):
		nLevels=len(self.levelColLists)
		wb=xlwt.Workbook()
		ws=wb.add_sheet('expenditures')
		styleTableTitle=xlwt.easyxf('font: bold on, height 240')
		styleHeader=xlwt.easyxf('font: bold on; align: wrap on')
		styleThinHeader=xlwt.easyxf('font: bold on, height 180; align: wrap on')
		styleVeryThinHeader=xlwt.easyxf('font: height 140; align: wrap on')
		styleStandard=xlwt.easyxf('')
		styleShallowStandard=xlwt.easyxf('font: bold on')
		styleAmount=xlwt.easyxf(num_format_str='#,##0.0;-#,##0.0;""')
		styleShallowAmount=xlwt.easyxf('font: bold on',num_format_str='#,##0.0;-#,##0.0;""')
		codeColumnsData={
			'departmentCode':	{'text':'Код ведомства',	'width':4,	'headerStyle':styleVeryThinHeader,	'cellStyle':styleStandard,'shallowCellStyle':styleShallowStandard},
			'superSectionCode':	{'text':'Код надраздела',	'width':5,	'headerStyle':styleThinHeader,		'cellStyle':styleStandard,'shallowCellStyle':styleShallowStandard},
			'sectionCode':		{'text':'Код раздела',		'width':5,	'headerStyle':styleThinHeader,		'cellStyle':styleStandard,'shallowCellStyle':styleShallowStandard},
			'categoryCode':		{'text':'Код целевой статьи',	'width':8,	'headerStyle':styleThinHeader,		'cellStyle':styleStandard,'shallowCellStyle':styleShallowStandard},
			'typeCode':		{'text':'Код вида расходов',	'width':4,	'headerStyle':styleVeryThinHeader,	'cellStyle':styleStandard,'shallowCellStyle':styleShallowStandard},
		}
		columns=[
			{'text':'Наименование','width':100,'headerStyle':styleHeader,'cellStyle':styleStandard,'shallowCellStyle':styleShallowStandard}
		]+[
			codeColumnsData[col] for cols in self.levelColLists for col in cols
		]+[
			{'text':'Сумма на '+str(year)+' г. (тыс. руб.)','width':15,'headerStyle':styleHeader,'cellStyle':styleAmount,'shallowCellStyle':styleShallowAmount} for year in self.years
		]
		ws.set_panes_frozen(True)
		ws.set_horz_split_pos(self.nHeaderRows)
		ws.row(0).height=400
		ws.merge(0,0,0,len(columns)-1)
		ws.write(0,0,tableTitle,styleTableTitle)
		ws.row(self.nHeaderRows-1).height=1200
		for nCol,col in enumerate(columns):
			ws.col(nCol).width=256*col['width']
			ws.write(self.nHeaderRows-1,nCol,col['text'],col['headerStyle'])
		for nRow,row in enumerate(self.outRows):
			for nCol,(cell,col) in enumerate(zip(row,columns)):
				shallow=self.levels[nRow]<nLevels//2
				style=col['shallowCellStyle' if shallow else 'cellStyle']
				if cell is None:
					continue
				elif type(cell) is str and cell[0]=='=':
					ws.write(self.nHeaderRows+nRow,nCol,xlwt.Formula(cell[1:]),style)
				else:
					ws.write(self.nHeaderRows+nRow,nCol,cell,style)
		wb.save(outputFilename)

with sqlite3.connect(':memory:') as conn:
	conn.row_factory=sqlite3.Row
	conn.execute('pragma foreign_keys=ON')
	conn.executescript(
		open('db/pr-bd-2014-16.sql',encoding='utf8').read()
	)

	LevelTable(
		[
			['departmentCode'],
			['sectionCode','categoryCode'],
			['typeCode'],
		],[
			'departmentName',
			'categoryName',
			'typeName',
		],
		[2014,2015,2016],
		conn.execute("""
			SELECT departmentName,categoryName,typeName,departmentCode,sectionCode,categoryCode,typeCode,year,amount
			FROM items
			JOIN departments USING(departmentCode)
			JOIN categories USING(categoryCode)
			JOIN types USING(typeCode)
			ORDER BY departmentOrder,sectionCode,categoryCode,typeCode,year
		""") # TODO filter years
	).makeXls(
		"Данные из приложений 3 и 4 к Закону Санкт-Петербурга «О бюджете Санкт-Петербурга на 2014 год и на плановый период 2015 и 2016 годов»",
		'out/pr03,04-2014-16.xls'
	)

	LevelTable(
		[
			['superSectionCode'],
			['sectionCode'],
			['categoryCode'],
			['typeCode'],
		],[
			'superSectionName',
			'sectionName',
			'categoryName',
			'typeName',
		],
		[2014,2015,2016],
		conn.execute("""
			SELECT superSectionName,sectionName,categoryName,typeName,superSectionCode,sectionCode,categoryCode,typeCode,year, SUM(amount) AS amount
			FROM items
			JOIN sections USING(sectionCode)
			JOIN superSections USING(superSectionCode)
			JOIN categories USING(categoryCode)
			JOIN types USING(typeCode)
			GROUP BY superSectionName,sectionName,categoryName,typeName,superSectionCode,sectionCode,categoryCode,typeCode,year
			ORDER BY superSectionCode,sectionCode,categoryCode,typeCode,year
		""") # TODO filter years
	).makeXls(
		"Данные из приложений 5 и 6 к Закону Санкт-Петербурга «О бюджете Санкт-Петербурга на 2014 год и на плановый период 2015 и 2016 годов»",
		'out/pr05,06-2014-16.xls'
	)
