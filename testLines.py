#!/usr/bin/env python3

import reporting.dbs,reporting.lines,reporting.spreadsheets,reporting.reports

with reporting.dbs.Sqlite('db/pr-bd-2014-16.sql') as db:
	rows=reporting.lines.SectionRows()
	rowsData=rows.getData(db)
	cols=reporting.lines.AmendmentCols()
	colsData=cols.getData(db)
