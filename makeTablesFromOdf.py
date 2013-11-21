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
				elif row[0].value.strip()=='.1.': # quirk in 3765.10.3
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
	def __init__(self,years):
		self.years=years
		self.paragraphNumber=None
	def setParagraphNumber(self,paragraphNumber):
		self.paragraphNumber=paragraphNumber
	def write(self,table,amendmentNumber):
		if not self.paragraphNumber:
			raise Exception('paragraph number for table not set')
		tableWriters.DepartmentTableWriter(
			makeTableReaderFromOdfTable(table),
                        amendmentNumber,self.years
		).write('tables/3765.'+self.paragraphNumber+'csv')
		self.paragraphNumber=None

# paragraphRe=re.compile(r'Пункт N (?P<paragraphNumber>\d+(?:\.\d+)*)')
amendParagraphTextRe=re.compile(r'(?P<paragraphNumber>(?:\d+\.)+) В текстовую часть')
amendParagraphAppendixRe=re.compile(r'(?P<paragraphNumber>(?:\d+\.)+) В приложение (?P<appendixNumber>\d+)')
amendAppendixRe=re.compile(r'В приложение (?P<appendixNumber>\d+)')
subParagraphRe=re.compile(r'\s+(?P<paragraphNumber>(?:\d+\.){2,})')

doc=ezodf.opendoc('assembly/3765.odt')
tableWriteWatcher=None
amendmentNumber=0
for obj in doc.body:
	if type(obj) is ezodf.text.Paragraph:
		print('paragraph {')
		for line in obj.plaintext().splitlines():
			# m=paragraphRe.match(line)
			# if m:
				# print('== paragraph',m.group('paragraphNumber'),'==')
			m=amendParagraphTextRe.match(line)
			if m:
				print('== amendment',m.group('paragraphNumber'),'for text ==')
				tableWriteWatcher=None
			m=amendParagraphAppendixRe.match(line)
			if m:
				print('== amendment',m.group('paragraphNumber'),'for appendix',m.group('appendixNumber'),'==')
				if m.group('appendixNumber') in ('3','4'):
					tableWriteWatcher=TableWriteWatcher([2014] if m.group('appendixNumber')=='3' else [2015,2016])
					tableWriteWatcher.setParagraphNumber(m.group('paragraphNumber'))
				else:
					tableWriteWatcher=None
			m=amendAppendixRe.match(line)
			if m:
				print('== amendment TBD for appendix',m.group('appendixNumber'),'==')
				if m.group('appendixNumber') in ('3','4'):
					tableWriteWatcher=TableWriteWatcher([2014] if m.group('appendixNumber')=='3' else [2015,2016])
				else:
					tableWriteWatcher=None
			m=subParagraphRe.match(line)
			if m:
				print('=== amendment',m.group('paragraphNumber'),'===')
				if tableWriteWatcher:
					tableWriteWatcher.setParagraphNumber(m.group('paragraphNumber'))
			print('line:',line)
		print('}')
	elif type(obj) is ezodf.table.Table:
		print('table',obj.nrows(),'x',obj.ncols())
		if tableWriteWatcher:
			amendmentNumber+=1
			tableWriteWatcher.write(obj,amendmentNumber)
