#!/usr/bin/env python3

from decimal import Decimal
import collections
import copy
import sqlite3

import xlwt3 as xlwt
import xlsxwriter

class LevelTable:
	def __init__(self,levelColLists,levelNames,yearsInAppendices,rows,nHeaderRows=2):
		self.levelColLists=levelColLists
		self.yearsInAppendices=yearsInAppendices
		self.years=[year for appendix,years in sorted(yearsInAppendices.items()) for year in years]
		self.nHeaderRows=nHeaderRows

		self.outRows=[[None]*len(self.yearsInAppendices)+['Итого']+[None for levelColList in self.levelColLists for col in levelColList]+[None]*len(self.years)]
		self.levels=[-1]
		self.formulaValues=collections.defaultdict(lambda: collections.defaultdict(lambda: Decimal(0)))

		def outputLevelRow(row,level):
			outRow=[None]*len(self.yearsInAppendices)
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
		nRow=0

		def makeClearSumsForLevel(level):
			levelSummands=copy.deepcopy(summands[level+1])
			levelSums=copy.deepcopy(sums[level+1])
			def getColChar(n):
				a=ord('A')
				radix=ord('Z')-a+1
				if n<radix:
					return chr(a+n)
				else:
					return chr(a+n//radix-1)+chr(a+n%radix)
			def fn(clearRow):
				if level<nLevels and levelSummands:
					for y in range(len(self.years)):
						colChar=getColChar(nFirstAmountCol+y)
						# +
						# self.outRows[levelSums][nFirstAmountCol+y]='='+'+'.join(
							# colChar+str(1+self.nHeaderRows+summand) for summand in levelSummands
						# )
						# SUBTOTAL
						self.outRows[levelSums][nFirstAmountCol+y]='=SUBTOTAL(9,'+colChar+str(1+self.nHeaderRows+levelSums)+':'+colChar+str(1+self.nHeaderRows+clearRow-1)+')'
						#
						self.formulaValues[levelSums][nFirstAmountCol+y]=sum(
							self.formulaValues[summand][nFirstAmountCol+y] for summand in levelSummands
						)
			return fn

		def putAppendixNumber(nCol):
			if self.outRows[-1][nCol]:
				return
			nRow=len(self.outRows)-1
			level=self.levels[nRow]
			putForLevels=[(level,nRow)]
			while True:
				nRow-=1
				if self.levels[nRow]<0:
					break
				if self.levels[nRow]>level or (self.levels[nRow]==level and not self.outRows[nRow][nCol]):
					continue
				if self.outRows[nRow][nCol]:
					break
				assert self.levels[nRow]==level-1, 'on row,col '+str(nRow)+','+str(nCol)+' met level '+str(self.levels[nRow])+' while on level '+str(level)
				level-=1
				putForLevels.insert(0,(level,nRow))
			nRow0=nRow
			for level,nRow in putForLevels:
				if self.levels[nRow0]==level-1:
					if self.outRows[nRow0][nCol] is None:
						self.outRows[nRow][nCol]='1.'
					else:
						self.outRows[nRow][nCol]=self.outRows[nRow0][nCol]+'1.'
				else:
					assert self.levels[nRow0]==level
					a=str(self.outRows[nRow0][nCol]).split('.')
					a[-2]=str(int(a[-2])+1)
					self.outRows[nRow][nCol]='.'.join(a)
				nRow0=nRow

		for row in rows:
			clearRow=0
			clearStack=[]
			for level,levelColList in enumerate(self.levelColLists):
				nextInside=tuple(row[col] for col in levelColList)
				if clearRow or insides[level]!=nextInside:
					nRow+=1
					clearStack.append(makeClearSumsForLevel(level))
					summands[level+1]=[]
					sums[level+1]=nRow
					summands[level].append(nRow)
					outRow=outputLevelRow(row,level)
					self.outRows.append(outRow)
					self.levels.append(level)
					insides[level]=nextInside
					if not clearRow:
						clearRow=nRow
			for fn in reversed(clearStack):
				fn(clearRow)
			nCol=nFirstAmountCol+self.years.index(row['year'])
			self.formulaValues[nRow][nCol]=outRow[nCol]=Decimal(row['amount'])/1000
			for nCol,(appendix,yearsInAppendix) in enumerate(self.yearsInAppendices.items()):
				if row['year'] in yearsInAppendix:
					putAppendixNumber(nCol)
		clearStack=[]
		for level in range(-1,nLevels):
			clearStack.append(makeClearSumsForLevel(level))
		for fn in reversed(clearStack):
			fn(nRow+1)

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
			{'text':'№ в приложении '+str(appendix),'width':10,'headerStyle':styleThinHeader,'cellStyle':styleStandard,'shallowCellStyle':styleShallowStandard} for appendix in self.yearsInAppendices
		]+[
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
			{'text':'№ в приложении '+str(appendix),'width':10,'headerStyle':styleThinHeader,'cellStyle':styleStandard,'shallowCellStyle':styleShallowStandard,'writer':ws.write_string} for appendix in self.yearsInAppendices
		]+[
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

	# dept table
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
		{3:[2014],4:[2015,2016]},
		conn.execute("""
			SELECT departmentName,categoryName,typeName,departmentCode,sectionCode,categoryCode,typeCode,year,amount
			FROM items
			JOIN departments USING(departmentCode)
			JOIN categories USING(categoryCode)
			JOIN types USING(typeCode)
			WHERE amendmentNumber=0
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

	# section table
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
		{5:[2014],6:[2015,2016]},
		conn.execute("""
			SELECT superSectionName,sectionName,categoryName,typeName,superSectionCode,sectionCode,categoryCode,typeCode,year, SUM(amount) AS amount
			FROM items
			JOIN sections USING(sectionCode)
			JOIN superSections USING(superSectionCode)
			JOIN categories USING(categoryCode)
			JOIN types USING(typeCode)
			WHERE amendmentNumber=0
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

	# governor amendments table
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
		{3:[2014],4:[2015,2016]},
		conn.execute("""
			SELECT departmentName,categoryName,typeName,departmentCode,sectionCode,categoryCode,typeCode,year, SUM(amount) AS amount
			FROM items
			JOIN departments USING(departmentCode)
			JOIN categories USING(categoryCode)
			JOIN types USING(typeCode)
			WHERE amendmentNumber>0
			GROUP BY departmentName,categoryName,typeName,departmentCode,sectionCode,categoryCode,typeCode,year
			ORDER BY departmentOrder,sectionCode,categoryCode,typeCode,year
		""") # TODO filter years
	)
	table.makeXlsx(
		"Поправка губернатора к Закону Санкт-Петербурга «О бюджете Санкт-Петербурга на 2014 год и на плановый период 2015 и 2016 годов»",
		'out/amendment-2014-16.xlsx'
	)

	# experimental project+amendments table
	fakeYears=[]
	for row in conn.execute("""
		SELECT DISTINCT year,amendmentNumber,documentNumber,paragraphNumber, year||'.'||documentNumber||'.'||paragraphNumber AS fakeYear
		FROM items
		JOIN amendments USING(amendmentNumber)
		ORDER BY year,amendmentNumber
	"""):
		# print(dict(row))
		fakeYears.append(row['fakeYear'])
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
		{0:fakeYears},
		conn.execute("""
			SELECT departmentName,categoryName,typeName,departmentCode,sectionCode,categoryCode,typeCode,
				year||'.'||documentNumber||'.'||paragraphNumber AS year,
				amount
			FROM items
			JOIN departments USING(departmentCode)
			JOIN categories USING(categoryCode)
			JOIN types USING(typeCode)
			JOIN amendments USING(amendmentNumber)
			ORDER BY departmentOrder,sectionCode,categoryCode,typeCode,year,amendmentNumber
		""") # TODO filter years
	)
	table.makeXlsx(
		"Данные из приложений 3 и 4 с поправками - ЭКПЕРИМЕНТАЛЬНО!",
		'out/project-amendments-2014-16.xlsx'
	)
