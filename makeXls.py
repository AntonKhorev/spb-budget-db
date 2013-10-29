#!/usr/bin/env python3

from decimal import Decimal
import collections
import copy
import sqlite3

import xlwt3 as xlwt
import xlsxwriter

class LevelTable:
	def __init__(self,levelColLists,levelNames,years,rows,nHeaderRows=2):
		self.levelColLists=levelColLists
		self.years=years
		self.nHeaderRows=nHeaderRows

		self.outRows=[['Итого']+[None for levelColList in self.levelColLists for col in levelColList]+[None]*len(self.years)]
		self.levels=[-1]
		self.formulaValues=collections.defaultdict(lambda: collections.defaultdict(lambda: Decimal(0)))

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
		nFirstAmountCol=len(self.outRows[0])-len(self.years)
		outRow=None
		insides=[None]*nLevels
		summands=[[]]+[None]*nLevels
		sums=[0]+[None]*nLevels
		def makeClearSumsForLevel(level):
			levelSummands=copy.deepcopy(summands[level+1])
			levelSums=copy.deepcopy(sums[level+1])
			def fn():
				if level<nLevels and levelSummands:
					for y in range(len(self.years)):
						colChar=chr(ord('A')+nFirstAmountCol+y)
						self.outRows[levelSums][nFirstAmountCol+y]='='+'+'.join(
							colChar+str(1+self.nHeaderRows+summand) for summand in levelSummands
						) # TODO SUBTOTAL()
						self.formulaValues[levelSums][nFirstAmountCol+y]=sum(
							self.formulaValues[summand][nFirstAmountCol+y] for summand in levelSummands
						)
			return fn

		nRow=0
		for row in rows:
			clear=False
			clearStack=[]
			for level,levelColList in enumerate(self.levelColLists):
				nextInside=tuple(row[col] for col in levelColList)
				if clear or insides[level]!=nextInside:
					nRow+=1
					clearStack.append(makeClearSumsForLevel(level))
					summands[level+1]=[]
					sums[level+1]=nRow
					summands[level].append(nRow)
					outRow=outputLevelRow(row,level)
					self.outRows.append(outRow)
					self.levels.append(level)
					insides[level]=nextInside
					clear=True
			for fn in reversed(clearStack):
				fn()
			nCol=nFirstAmountCol+self.years.index(row['year'])
			self.formulaValues[nRow][nCol]=outRow[nCol]=Decimal(row['amount'])/1000
		clearStack=[]
		for level in range(-1,nLevels):
			clearStack.append(makeClearSumsForLevel(level))
		for fn in reversed(clearStack):
			fn()

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

	def makeXlsx(self,tableTitle,outputFilename):
		nLevels=len(self.levelColLists)
		wb=xlsxwriter.Workbook(outputFilename)
		ws=wb.add_worksheet('expenditures')
		styleTableTitle=wb.add_format({'bold':True,'font_size':13})
		styleHeader=wb.add_format({'bold':True,'text_wrap':True})
		styleThinHeader=wb.add_format({'bold':True,'font_size':10,'text_wrap':True})
		styleVeryThinHeader=wb.add_format({'font_size':8,'text_wrap':True})
		styleStandard=wb.add_format()
		styleShallowStandard=wb.add_format({'bold':True})
		styleCentered=wb.add_format({'align':'center'})
		styleShallowCentered=wb.add_format({'bold':True,'align':'center'})
		styleAmount=wb.add_format({'num_format':'#,##0.0;-#,##0.0;""'})
		styleShallowAmount=wb.add_format({'bold':True,'num_format':'#,##0.0;-#,##0.0;""'})
		def numericWriter(nRow,nCol,cell,style):
			if type(cell) is str and cell[0]=='=':
				ws.write_formula(nRow,nCol,cell,style,self.formulaValues[nRow-self.nHeaderRows][nCol])
			else:
				ws.write_number(nRow,nCol,cell,style)
		codeColumnsData={
			'departmentCode':	{'text':'Код ведомства',	'width':4,	'headerStyle':styleVeryThinHeader,	'cellStyle':styleCentered,'shallowCellStyle':styleShallowCentered,	'writer':ws.write_string},
			'superSectionCode':	{'text':'Код надраздела',	'width':5,	'headerStyle':styleThinHeader,		'cellStyle':styleCentered,'shallowCellStyle':styleShallowCentered,	'writer':ws.write_string},
			'sectionCode':		{'text':'Код раздела',		'width':5,	'headerStyle':styleThinHeader,		'cellStyle':styleCentered,'shallowCellStyle':styleShallowCentered,	'writer':ws.write_string},
			'categoryCode':		{'text':'Код целевой статьи',	'width':8,	'headerStyle':styleThinHeader,		'cellStyle':styleCentered,'shallowCellStyle':styleShallowCentered,	'writer':ws.write_string},
			'typeCode':		{'text':'Код вида расходов',	'width':4,	'headerStyle':styleVeryThinHeader,	'cellStyle':styleCentered,'shallowCellStyle':styleShallowCentered,	'writer':ws.write_string},
		}
		columns=[
			{'text':'Наименование','width':100,'headerStyle':styleHeader,'cellStyle':styleStandard,'shallowCellStyle':styleShallowStandard,'writer':ws.write_string}
		]+[
			codeColumnsData[col] for cols in self.levelColLists for col in cols
		]+[
			{'text':'Сумма на '+str(year)+' г. (тыс. руб.)','width':15,'headerStyle':styleHeader,'cellStyle':styleAmount,'shallowCellStyle':styleShallowAmount,'writer':numericWriter} for year in self.years
		]
		ws.freeze_panes(self.nHeaderRows,0)
		ws.set_row(0,22)
		ws.merge_range(0,0,0,len(columns)-1,tableTitle,styleTableTitle)
		ws.set_row(self.nHeaderRows-1,60)
		for nCol,col in enumerate(columns):
			ws.set_column(nCol,nCol,col['width'])
			ws.write(self.nHeaderRows-1,nCol,col['text'],col['headerStyle'])
		for nRow,row in enumerate(self.outRows):
			if self.levels[nRow]>=0:
				ws.set_row(self.nHeaderRows+nRow,options={'level':self.levels[nRow]+1})
			for nCol,(cell,col) in enumerate(zip(row,columns)):
				shallow=self.levels[nRow]<nLevels//2
				style=col['shallowCellStyle' if shallow else 'cellStyle']
				if cell is None:
					continue
				col['writer'](self.nHeaderRows+nRow,nCol,cell,style)
		wb.close()

with sqlite3.connect(':memory:') as conn:
	conn.row_factory=sqlite3.Row
	conn.execute('pragma foreign_keys=ON')
	conn.executescript(
		open('db/pr-bd-2014-16.sql',encoding='utf8').read()
	)

	table=LevelTable(
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
	)
	table.makeXls(
		"Данные из приложений 3 и 4 к Закону Санкт-Петербурга «О бюджете Санкт-Петербурга на 2014 год и на плановый период 2015 и 2016 годов»",
		'out/pr03,04-2014-16.xls'
	)
	table.makeXlsx(
		"Данные из приложений 3 и 4 к Закону Санкт-Петербурга «О бюджете Санкт-Петербурга на 2014 год и на плановый период 2015 и 2016 годов»",
		'out/pr03,04-2014-16.xlsx'
	)

	table=LevelTable(
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
	)
	table.makeXls(
		"Данные из приложений 5 и 6 к Закону Санкт-Петербурга «О бюджете Санкт-Петербурга на 2014 год и на плановый период 2015 и 2016 годов»",
		'out/pr05,06-2014-16.xls'
	)
	table.makeXlsx(
		"Данные из приложений 5 и 6 к Закону Санкт-Петербурга «О бюджете Санкт-Петербурга на 2014 год и на плановый период 2015 и 2016 годов»",
		'out/pr05,06-2014-16.xlsx'
	)
