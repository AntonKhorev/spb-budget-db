#!/usr/bin/env python3

import decimal
from openpyxl import load_workbook
import tableWriters

def makeTableReaderFromXlsxFile(inputFilename):
	def makeDecimalAmount(amount):
		if type(amount) is int:
			amount=str(amount)+'.0'
		else:
			amount=str(amount)
		return decimal.Decimal(amount)
	def reader(years):
		wb=load_workbook(inputFilename)
		ws=wb.get_active_sheet()
		maxRow=ws.get_highest_row()
		for nRow in range(maxRow):
			if ws.cell(row=nRow,column=0).value==1:
				break
		else:
			raise Exception('table start not found')
		for nRow in range(nRow,maxRow):
			yield (
				(ws.cell(row=nRow,column=c).value for c in range(5)),
				[makeDecimalAmount(ws.cell(row=nRow,column=c).value) for c in range(5,5+len(years))]
			)
	return reader

documentNumber=3574
tableWriters.DepartmentTableWriter(
	makeTableReaderFromXlsxFile('fincom/pr03-2014-16.xlsx'),
	[2014]
).write('tables/department.'+str(documentNumber)+'.3.csv')
tableWriters.DepartmentTableWriter(
	makeTableReaderFromXlsxFile('fincom/pr04-2014-16.xlsx'),
	[2015,2016]
).write('tables/department.'+str(documentNumber)+'.4.csv')
tableWriters.SectionTableWriter(
	makeTableReaderFromXlsxFile('fincom/pr05-2014-16.xlsx'),
	[2014]
).write('tables/section.'+str(documentNumber)+'.5.csv')
tableWriters.SectionTableWriter(
	makeTableReaderFromXlsxFile('fincom/pr06-2014-16.xlsx'),
	[2015,2016]
).write('tables/section.'+str(documentNumber)+'.6.csv')
