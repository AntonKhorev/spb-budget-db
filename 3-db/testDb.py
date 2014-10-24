#!/usr/bin/env python3

import sqlite3

inputFilename='../3-db.out/db.sql'

with sqlite3.connect(':memory:') as conn:
	conn.execute('pragma foreign_keys=ON')

	# conn.executescript(
		# open(inputFilename,encoding='utf8').read()
	# )

	# load command by command
	for command in open(inputFilename,encoding='utf8').read().split(';\n'):
		print('>',command)
		conn.execute(command)

	# for row in conn.execute("SELECT departmentCode, departmentName FROM departments ORDER BY departmentOrder"):
		# print(row)
	# for row in conn.execute("SELECT * FROM categories ORDER BY categoryCode"):
		# print(row)
	# for row in conn.execute("SELECT * FROM types ORDER BY typeCode"):
		# print(row)
	# for row in conn.execute("""
		# SELECT fiscalYear,departmentCode,departmentName,SUM(amount)
		# FROM items
		# JOIN departments USING(departmentCode)
		# GROUP BY fiscalYear,departmentCode,departmentName
		# ORDER BY departmentCode,departmentName,fiscalYear
	# """):
		# print(row)
	for row in conn.execute("""
		SELECT documentNumber,authorLongName
		FROM documents
		LEFT JOIN authors USING(authorId)
		ORDER BY documentNumber
	"""):
		print(row)
