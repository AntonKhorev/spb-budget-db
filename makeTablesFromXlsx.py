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

# project
documentNumber=3574
tableWriters.DepartmentTableWriter(
	makeTableReaderFromXlsxFile('fincom/2014.0.p/pr03-2014-16.xlsx'),
	[2014]
).write('tables/department.edit.'+str(documentNumber)+'.3.csv')
tableWriters.DepartmentTableWriter(
	makeTableReaderFromXlsxFile('fincom/2014.0.p/pr04-2014-16.xlsx'),
	[2015,2016]
).write('tables/department.edit.'+str(documentNumber)+'.4.csv')
tableWriters.SectionTableWriter(
	makeTableReaderFromXlsxFile('fincom/2014.0.p/pr05-2014-16.xlsx'),
	[2014]
).write('tables/section.edit.'+str(documentNumber)+'.5.csv')
tableWriters.SectionTableWriter(
	makeTableReaderFromXlsxFile('fincom/2014.0.p/pr06-2014-16.xlsx'),
	[2015,2016]
).write('tables/section.edit.'+str(documentNumber)+'.6.csv')

# law
documentNumber=3781
tableWriters.DepartmentTableWriter(
	makeTableReaderFromXlsxFile('fincom/2014.0.z/pr03_bd2014-16.xlsx'),
	[2014]
).write('tables/department.sum.'+str(documentNumber)+'.3.csv')
tableWriters.DepartmentTableWriter(
	makeTableReaderFromXlsxFile('fincom/2014.0.z/pr04_bd2014-16.xlsx'),
	[2015,2016]
).write('tables/department.sum.'+str(documentNumber)+'.4.csv')
tableWriters.SectionTableWriter(
	makeTableReaderFromXlsxFile('fincom/2014.0.z/pr05_bd2014-16.xlsx'),
	[2014]
).write('tables/section.sum.'+str(documentNumber)+'.5.csv')
tableWriters.SectionTableWriter(
	makeTableReaderFromXlsxFile('fincom/2014.0.z/pr06_bd2014-16.xlsx'),
	[2015,2016]
).write('tables/section.sum.'+str(documentNumber)+'.6.csv')
