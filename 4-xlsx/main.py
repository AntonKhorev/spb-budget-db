#!/usr/bin/env python3

inputFilename='../3-db.out/db2015.sql'
outputDirectory='../4-xlsx.out'
import os
if not os.path.exists(outputDirectory):
	os.makedirs(outputDirectory)

import dbs,lines,spreadsheets,reports

with dbs.Sqlite(inputFilename) as db:
	reports.Report(
		db,
		lines.DepartmentRows(),
		lines.AmendmentCols(),
		"Ведомственная структура расходов бюджета Санкт-Петербурга"
	).save(
		spreadsheets.XlsxSpreadsheet(outputDirectory+'/departments2015.xlsx')
	)
	reports.Report(
		db,
		lines.SectionRows(),
		lines.AmendmentCols(),
		"Функциональная структура расходов бюджета Санкт-Петербурга"
	).save(
		spreadsheets.XlsxSpreadsheet(outputDirectory+'/sections2015.xlsx')
	)
