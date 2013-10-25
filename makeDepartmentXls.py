#!/usr/bin/env python3

import sqlite3

with sqlite3.connect(':memory:') as conn:
	conn.execute('pragma foreign_keys=ON')
	conn.executescript(
		open('db/pr-bd-2014-16.sql',encoding='utf8').read()
	)
	for row in conn.execute("""
		SELECT departmentName,categoryName,typeName,sectionCode,categoryCode,typeCode,year,amount
		FROM items
		JOIN departments USING(departmentCode)
		JOIN categories USING(categoryCode)
		JOIN types USING(typeCode)
		ORDER BY departmentOrder,sectionCode,categoryCode,typeCode,year
	"""):
		print(row)
