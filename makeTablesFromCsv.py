#!/usr/bin/env python3
import tableWriters
import csv

def makeTableReaderFromCsvFile(inputFilename,nAmountCols):
	def makeAmount(amount):
		return amount.replace(',','.')
	def makeRow(row):
		return row[:5]+[makeAmount(a) for a in row[5:5+nAmountCols]]
	with open(inputFilename,encoding='utf8',newline='') as inputFile:
		reader=csv.reader(inputFile)
		next(reader)
		totalRow=next(reader)
		for row in reader:
			yield makeRow(row)
		yield makeRow(totalRow)

# project of 1st correction
documentNumber=4597
tableWriters.DepartmentTableWriter(
	makeTableReaderFromCsvFile('fincom/2014.1.p/2014.1.p-2014(3).csv',1),
	[2014]
).write('tables/2014.1.p.'+str(documentNumber)+'.3.department.set(2014).csv')
tableWriters.DepartmentTableWriter(
	makeTableReaderFromCsvFile('fincom/2014.1.p/2014.1.p-2015,2016(3).csv',2),
	[2015,2016]
).write('tables/2014.1.p.'+str(documentNumber)+'.4.department.diff.csv')
