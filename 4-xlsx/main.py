#!/usr/bin/env python3

import dbs,lines,spreadsheets,reports

inputFilename='../3-db.out/db.sql'
outputDirectory='../4-xlsx.out'

with dbs.Sqlite(inputFilename) as db:
	reports.Report(
		db,
		lines.DepartmentRows(),
		lines.AmendmentCols(),
		"Ведомственная структура расходов бюджета Санкт-Петербурга"
	).save(
		spreadsheets.XlsxSpreadsheet(outputDirectory+'/departments.xlsx')
	)
	reports.Report(
		db,
		lines.SectionRows(),
		lines.AmendmentCols(),
		"Функциональная структура расходов бюджета Санкт-Петербурга"
	).save(
		spreadsheets.XlsxSpreadsheet(outputDirectory+'/sections.xlsx')
	)
