#!/usr/bin/env python3

import dbs,lines,spreadsheets,reports

inputFilename='../3-db.out/db.sql'

with dbs.Sqlite(inputFilename) as db:
	rows=lines.SectionRows()
	rowsData=rows.getData(db)
	cols=lines.AmendmentCols()
	colsData=cols.getData(db)
