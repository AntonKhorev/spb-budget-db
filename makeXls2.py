#!/usr/bin/env python3

import sqlite3
import reporting.lines,reporting.spreadsheets,reporting.reports

with sqlite3.connect(':memory:') as conn:
	conn.row_factory=sqlite3.Row
	conn.execute('pragma foreign_keys=ON')
	conn.executescript(
		open('db/pr-bd-2014-16.sql',encoding='utf8').read()
	)
	reporting.reports.Report(
		conn,
		reporting.lines.DepartmentRows(),
		reporting.lines.AmendmentCols()
	).save(
		reporting.spreadsheets.XlsxSpreadsheet('out2/dept.xlsx')
	)
	reporting.reports.Report(
		conn,
		reporting.lines.SectionRows(),
		reporting.lines.AmendmentCols()
	).save(
		reporting.spreadsheets.XlsxSpreadsheet('out2/sect.xlsx')
	)
