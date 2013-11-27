#!/usr/bin/env python3

import decimal
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
			categoryCode=row[4].value.strip()
			if categoryCode:
				categoryCode=categoryCode.zfill(7)
			sc1=row[2].value.strip()
			sc2=row[3].value.strip()
			if sc1:
				sc1=sc1.zfill(2)
			if sc2:
				sc2=sc2.zfill(2)
			sectionCode=sc1+sc2
			keys=(row[0].value.strip(),row[1].value.strip(),sectionCode,categoryCode,row[5].value.strip())
			def makeAmount(cell):
				amount=cell.value.strip()
				if '.' not in amount:
					# quirk in 3765.7.1.1 and 3765.7.5.1
					amount=amount[:-1]+'.'+amount[-1]
				elif amount.count('.')==2:
					# quirk in 3781.2.34.7.1.
					amount=amount.replace('.','',1)
				return decimal.Decimal(amount)
			amounts=[makeAmount(row[i]) for i in range(6,6+len(years))]
			yield (keys,amounts)
		if not found:
			raise Exception('table start not found')
	return reader

class TableWriteWatcher:
	def __init__(self,years):
		self.years=years
		self.paragraphNumber=None
	def setParagraphNumber(self,paragraphNumber):
		self.paragraphNumber=paragraphNumber
	def write(self,table,documentNumber,amendmentNumber):
		# print('writing table for amendment',self.paragraphNumber)
		if not self.paragraphNumber:
			raise Exception('paragraph number for table not set')
		tableWriters.DepartmentTableWriter(
			makeTableReaderFromOdfTable(table),
                        amendmentNumber,self.years
		).write('tables/'+documentNumber+'.'+self.paragraphNumber+'csv')
		self.paragraphNumber=None

# paragraphRe=re.compile(r'Пункт N (?P<paragraphNumber>\d+(?:\.\d+)*)')
amendParagraphTextRe=re.compile(r'(?P<paragraphNumber>(?:\d+\.)+) В текстовую часть')
amendParagraphAppendixRe=re.compile(r'(?P<paragraphNumber>(?:\d+\.)+) В приложение (?P<appendixNumber>\d+)')
amendAppendixRe=re.compile(r'В приложение (?P<appendixNumber>\d+)')
subParagraphRe=re.compile(r'\s+(?P<paragraphNumber>(?:\d+\.){2,})')

amendmentNumber=0
for documentNumber in ('3765','3781'):
	filename='assembly/'+documentNumber+'.odt'
	doc=ezodf.opendoc(filename)
	tableWriteWatcher=None
	for obj in doc.body:
		if type(obj) is ezodf.text.Paragraph:
			# print('paragraph {')
			for line in obj.plaintext().splitlines():
				# m=paragraphRe.match(line)
				# if m:
					# print('== paragraph',m.group('paragraphNumber'),'==')
				m=amendParagraphTextRe.match(line)
				if m:
					# print('== amendment',m.group('paragraphNumber'),'for text ==')
					tableWriteWatcher=None
				m=amendParagraphAppendixRe.match(line)
				if m:
					# print('== amendment',m.group('paragraphNumber'),'for appendix',m.group('appendixNumber'),'==')
					if m.group('appendixNumber') in ('3','4'):
						tableWriteWatcher=TableWriteWatcher([2014] if m.group('appendixNumber')=='3' else [2015,2016])
						tableWriteWatcher.setParagraphNumber(m.group('paragraphNumber'))
					else:
						tableWriteWatcher=None
				m=amendAppendixRe.match(line)
				if m:
					# print('== amendment TBD for appendix',m.group('appendixNumber'),'==')
					if m.group('appendixNumber') in ('3','4'):
						tableWriteWatcher=TableWriteWatcher([2014] if m.group('appendixNumber')=='3' else [2015,2016])
					else:
						tableWriteWatcher=None
				m=subParagraphRe.match(line)
				if m:
					# print('=== amendment',m.group('paragraphNumber'),'===')
					if tableWriteWatcher:
						tableWriteWatcher.setParagraphNumber(m.group('paragraphNumber'))
				# print('line:',line)
			# print('}')
		elif type(obj) is ezodf.table.Table:
			# print('table',obj.nrows(),'x',obj.ncols())
			if tableWriteWatcher:
				amendmentNumber+=1
				tableWriteWatcher.write(obj,documentNumber,amendmentNumber)
