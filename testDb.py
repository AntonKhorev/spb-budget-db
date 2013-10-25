#!/usr/bin/env python3

import sqlite3

with sqlite3.connect(':memory:') as conn:
	conn.execute('pragma foreign_keys=ON')
	conn.executescript(
		open('db/pr-bd-2014-16.sql',encoding='utf8').read()
	)
	# for row in conn.execute("SELECT departmentCode, departmentName FROM departments ORDER BY departmentOrder"):
		# print(row)
	# for row in conn.execute("SELECT * FROM categories ORDER BY categoryCode"):
		# print(row)
	# for row in conn.execute("SELECT * FROM types ORDER BY typeCode"):
		# print(row)
	for row in conn.execute("""
		SELECT year,departmentCode,departmentName,SUM(amount)
		FROM items
		JOIN departments USING(departmentCode)
		GROUP BY year,departmentCode,departmentName
		ORDER BY departmentCode,departmentName,year
	"""):
		print(row)
