#!/usr/bin/env python3

import reporting.dbs,reporting.lines,reporting.spreadsheets,reporting.reports

# with sqlite3.connect(':memory:') as conn:
	# conn.row_factory=sqlite3.Row
	# conn.execute('pragma foreign_keys=ON')
	# conn.executescript(
		# open('db/pr-bd-2014-16.sql',encoding='utf8').read()
	# )
with reporting.dbs.Sqlite('db/pr-bd-2014-16.sql') as db:
	reporting.reports.Report(
		db,
		reporting.lines.DepartmentRows(),
		reporting.lines.AmendmentCols(),
		"Ведомственная структура расходов бюджета Санкт-Петербурга"
	).save(
		reporting.spreadsheets.XlsxSpreadsheet('out2/dept.xlsx')
	)
	reporting.reports.Report(
		db,
		reporting.lines.SectionRows(),
		reporting.lines.AmendmentCols(),
		"Функциональная структура расходов бюджета Санкт-Петербурга"
	).save(
		reporting.spreadsheets.XlsxSpreadsheet('out2/sect.xlsx')
	)
