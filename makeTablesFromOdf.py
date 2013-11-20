#!/usr/bin/env python3

import re
import ezodf
import tableWriters

def makeTableReaderFromOdfTable(table):
	def reader(years):
		found=False
		for row in obj.rows():
			if not found:
				if row[0].value.strip()=='1.':
					found=True
				else:
					continue
			yield (
				(row[0].value.strip(),row[1].value.strip(),row[2].value.strip()+row[3].value.strip(),row[4].value.strip(),row[5].value.strip()),
				[row[i].value.strip() for i in range(6,6+len(years))]
			)
		if not found:
			raise Exception('table start not found')
	return reader

class TableWriteWatcher:
	def __init__(self,paragraphNumber,years):
		self.paragraphNumber=paragraphNumber
		self.years=years
		self.wrote=False
	def write(self,table):
		if self.wrote:
			raise Exception('already wrote')
		tableWriters.DepartmentTableWriter(
			makeTableReaderFromOdfTable(table),
                        self.years
		).write('tables/3765.'+self.paragraphNumber+'csv')
		self.wrote=True

paragraphRe=re.compile(r'Пункт N (?P<paragraphNumber>\d+(?:\.\d+)*)')
amendTextRe=re.compile(r'(?P<paragraphNumber>(?:\d+\.)+) В текстовую часть')
amendAppendixRe=re.compile(r'(?P<paragraphNumber>(?:\d+\.)+) В приложение (?P<appendixNumber>\d+)')

doc=ezodf.opendoc('assembly/3765.odt')
tableWriteWatcher=None
for obj in doc.body:
	if type(obj) is ezodf.text.Paragraph:
		print('text paragraph {')
		for line in obj.plaintext().splitlines():
			m=paragraphRe.match(line)
			if m:
				print('=== paragraph',m.group('paragraphNumber'),'===')
			m=amendTextRe.match(line)
			if m:
				print('=== amendment',m.group('paragraphNumber'),'for text ===')
			m=amendAppendixRe.match(line)
			if m:
				print('=== amendment',m.group('paragraphNumber'),'for appendix',m.group('appendixNumber'),'===')
				if m.group('appendixNumber') in ('3','4'):
					print('===*** got to process it ***===')
					tableWriteWatcher=TableWriteWatcher(m.group('paragraphNumber'),([2014] if m.group('appendixNumber')=='3' else [2015,2016]))
				else:
					tableWriteWatcher=None
			print('text line:',line)
		print('}')
	elif type(obj) is ezodf.table.Table:
		print('table',obj.nrows(),'x',obj.ncols(),'{')
		for i,row in enumerate(obj.rows()):
			for j,cell in enumerate(row):
				print('[',i,j,']',cell.value)
		print('}')
		if tableWriteWatcher:
			tableWriteWatcher.write(obj)
