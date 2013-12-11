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
			name=row[1].value.strip()
			typeCode=row[5].value.strip()
			if typeCode=='00': # quirk in 3781.2.11.14.1
				if name=='Предоставление субсидий бюджетным, автономным учреждениям и иным некоммерческим организациям':
					typeCode='600'
				else:
					raise Exception('unknown quirk')
			if name=='Предоставление субсидий бюджетным, автономным учреждениям и иным некоммерческим организациям' and categoryCode=='4310270': # quirk in 3781.2.12.4.1
				categoryCode='4310170'
			keys=(row[0].value.strip(),name,sectionCode,categoryCode,typeCode)
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
	def write(self,table,documentNumber):
		# print('writing table for amendment',self.paragraphNumber)
		if not self.paragraphNumber:
			raise Exception('paragraph number for table not set')
		tableWriters.DepartmentTableWriter(
			makeTableReaderFromOdfTable(table),
                        self.years
		).write('tables/2014.0.p.'+documentNumber+'.'+self.paragraphNumber+'department.csv')
		self.paragraphNumber=None

pn=r'(?P<paragraphNumber>(?:\d+\.)+)'
cc=r'(?P<categoryCode>\d{7})'
dnms=r'\(.*?распорядител. - (?P<departmentNames>.*?)\)'
# paragraphRe=re.compile(r'Пункт N '+pn)
amendParagraphTextRe=re.compile(pn+r' В текстовую часть')
amendParagraphAppendixRe=re.compile(pn+r' В приложение (?P<appendixNumber>\d+)')
amendAppendixRe=re.compile(r'В приложение (?P<appendixNumber>\d+)')
subParagraphRe=re.compile(r'\s+(?P<paragraphNumber>(?:\d+\.){2,})')

# regexes for move:
moveDepartmentRe=re.compile(r'\s*'+pn+r' Главного распорядителя "(?P<departmentName1>.*?)" в целевой статье '+cc+r' ".*?" изменить на "(?P<departmentName2>.*?)"')
moveSectionRe=re.compile(r'\s*'+pn+r' Подраздел (?P<sectionCode1>\d{4}) ".*?" в целевой статье '+cc+r' ".*?" '+dnms+r' изменить на (?P<sectionCode2>\d{4}) ".*?"')
moveCategoryRe=re.compile(r'\s*'+pn+r' Изложить наименование целевой статьи (?P<categoryCode1>\d{7}) ".*?" '+dnms+r' в следующей редакции: ".*?" с изменением кода целевой статьи на (?P<categoryCode2>\d{7})')
moveCategoryTypeRe=re.compile(r'\s*'+pn+r' Изложить наименование целевой статьи (?P<categoryCode1>\d{7}) ".*?" '+dnms+r' в следующей редакции: ".*?" с изменением кода целевой статьи на (?P<categoryCode2>\d{7}) и с изменением(?: кода)? вида расходов (?P<typeCode1>\d{3}) ".*?" на (?P<typeCode2>\d{3}) ".*?" по (?P<departmentNamesForType>.*?)\.')
moveTypeRe=re.compile(r'\s*'+pn+r' Код вида расходов (?P<typeCode1>\d{3}) ".*?" в целевой статье '+cc+r' ".*?" '+dnms+r' изменить на (?P<typeCode2>\d{3}) ".*?"')

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
				def getMoveFilename(m):
					return 'tables/2014.0.p.'+documentNumber+'.'+m.group('paragraphNumber')+'move.csv'
				def listDepartmentMoves(m,s,t,deptGroupName='departmentNames'):
					def processName(d):
						return d.replace('Администрации','Администрация')
					return ((processName(d),p1,p2,p3) for d in m.group(deptGroupName).split(', ') for p1,p2,p3 in (s,t))
				def writeMove(m,data):
					rows=list(data)
					years=[2014,2015,2016]
					def listData():
						return ((year,)+row for year in years for row in rows)
					tableWriters.writeMoveTable(getMoveFilename(m),listData())
				m=moveDepartmentRe.match(line)
				if m: writeMove(m,(
					(m.group('departmentName1'),'*',m.group('categoryCode'),'*'),
					(m.group('departmentName2'),'*',m.group('categoryCode'),'*')
				))
				m=moveSectionRe.match(line)
				if m: writeMove(m,listDepartmentMoves(m,
					(m.group('sectionCode1'),m.group('categoryCode'),'*'),
					(m.group('sectionCode2'),m.group('categoryCode'),'*')
				))
				m=moveCategoryTypeRe.match(line)
				if m:
					writeMove(m,list(listDepartmentMoves(m,
						('*',m.group('categoryCode1'),'*'),
						('*',m.group('categoryCode2'),'*')
					))+list(listDepartmentMoves(m,
						('*',m.group('categoryCode2'),m.group('typeCode1')),
						('*',m.group('categoryCode2'),m.group('typeCode2')),
						'departmentNamesForType'
					)))
				else:
					m=moveCategoryRe.match(line)
					if m:
						writeMove(m,listDepartmentMoves(m,
							('*',m.group('categoryCode1'),'*'),
							('*',m.group('categoryCode2'),'*')
						))
				m=moveTypeRe.match(line)
				if m: writeMove(m,listDepartmentMoves(m,
					('*',m.group('categoryCode'),m.group('typeCode1')),
					('*',m.group('categoryCode'),m.group('typeCode2'))
				))
			# print('}')
		elif type(obj) is ezodf.table.Table:
			# print('table',obj.nrows(),'x',obj.ncols())
			if tableWriteWatcher:
				tableWriteWatcher.write(obj,documentNumber)
