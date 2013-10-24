#!/usr/bin/env python3

import sqlite3

with sqlite3.connect(':memory:') as conn:
	conn.executescript(
		open('db/pr-bd-2014-16.sql',encoding='utf8').read()
	)
	conn.execute('pragma foreign_keys=ON')
	for row in conn.execute("SELECT departmentCode, departmentName FROM departments ORDER BY departmentOrder"):
		print(row)
