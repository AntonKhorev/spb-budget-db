#!/usr/bin/env python3

import decimal
import re
import csv

class TableWriter:
	def __init__(self,tableReader,years):
		self.years=years
		self.rows=[{}]*len(years) # reserve first rows for totals
		self.punctWithoutSpaceRe=re.compile(r'(?<=[.,])(?=[^\W\d_])')
		self.processTable(tableReader)

	def processName(self,name):
		name=' '.join(name.split())
		name=self.punctWithoutSpaceRe.sub(' ',name)
		return name

	def makePrependRow(self):
		nRow=0
		def addRow(row):
			nonlocal nRow
			self.rows[nRow]=row
			nRow+=1
		return addRow

	def processTable(self,tableReader):
		raise Exception('implement this')

	def getCols(self):
		raise Exception('implement this')

	def write(self,outputFilename):
		writer=csv.writer(open(outputFilename,'w',newline='',encoding='utf8'),quoting=csv.QUOTE_NONNUMERIC)
		cols=self.getCols()
		writer.writerow(cols)
		for row in self.rows:
			writer.writerow([row.get(col) for col in cols])

class DepartmentTableWriter(TableWriter):
	def processTable(self,tableReader):
		departmentNameRe=re.compile(r'(?P<departmentName>.*?)\s*\((?P<departmentCode>...)\)')
		for number,name,sectionCode,categoryCode,typeCode,*amounts in tableReader():
			amounts=[decimal.Decimal(amount) for amount in amounts]
			name=self.processName(name)
			sectionCode=sectionCode[:2]+sectionCode[-2:]
			typeCode=str(typeCode)
			amountCol=None
			row={}
			addRow=self.rows.append
			if not number:
				addRow=self.makePrependRow()
				amountCol='yAmount'
			elif not sectionCode:
				m=departmentNameRe.match(name)
				row['departmentName']=departmentName=m.group('departmentName')
				row['departmentCode']=departmentCode=m.group('departmentCode')
				amountCol='ydAmount'
			elif not typeCode:
				row['departmentName']=departmentName
				row['departmentCode']=departmentCode
				row['sectionCode']=sectionCode
				row['categoryName']=categoryName=name
				row['categoryCode']=categoryCode
				amountCol='ydssccAmount'
			else:
				row['departmentName']=departmentName
				row['departmentCode']=departmentCode
				row['sectionCode']=sectionCode
				row['categoryName']=categoryName
				row['categoryCode']=categoryCode
				row['typeName']=typeName=name
				row['typeCode']=typeCode
				amountCol='ydsscctAmount'
			for year,amount in zip(self.years,amounts):
				r=row.copy()
				r['year']=year
				r[amountCol]=amount
				addRow(r)
			if not number:
				break
		else:
			raise Exception('no total line found')

	def getCols(self):
		return [
			'year',
			'departmentName','departmentCode',
			'sectionCode','categoryName','categoryCode',
			'typeName','typeCode',
			'yAmount','ydAmount','ydssccAmount','ydsscctAmount',
		]

class SectionTableWriter(TableWriter):
	def processTable(self,tableReader):
		for number,name,sectionCode,categoryCode,typeCode,*amounts in tableReader():
			amounts=[decimal.Decimal(amount) for amount in amounts]
			name=self.processName(name)
			# sectionCode=sectionCode[:2]+sectionCode[-2:]
			if sectionCode[:2]!='  ':
				superSectionCode=sectionCode[:2]+'00'
			if sectionCode[-2:]!='  ':
				sectionCode=superSectionCode[:2]+sectionCode[-2:]
			else:
				sectionCode=''
			#
			typeCode=str(typeCode)
			amountCol=None
			row={}
			addRow=self.rows.append
			if not number:
				addRow=self.makePrependRow()
				amountCol='yAmount'
			elif not sectionCode:
				row['superSectionName']=superSectionName=name
				row['superSectionCode']=superSectionCode
				amountCol='ysAmount'
			elif not categoryCode:
				row['superSectionName']=superSectionName
				row['superSectionCode']=superSectionCode
				row['sectionName']=sectionName=name
				row['sectionCode']=sectionCode
				amountCol='yssAmount'
			elif not typeCode:
				row['superSectionName']=superSectionName
				row['superSectionCode']=superSectionCode
				row['sectionName']=sectionName
				row['sectionCode']=sectionCode
				row['categoryName']=categoryName=name
				row['categoryCode']=categoryCode
				amountCol='yssccAmount'
			else:
				row['superSectionName']=superSectionName
				row['superSectionCode']=superSectionCode
				row['sectionName']=sectionName
				row['sectionCode']=sectionCode
				row['categoryName']=categoryName
				row['categoryCode']=categoryCode
				row['typeName']=typeName=name
				row['typeCode']=typeCode
				amountCol='ysscctAmount'
			for year,amount in zip(self.years,amounts):
				r=row.copy()
				r['year']=year
				r[amountCol]=amount
				addRow(r)
			if not number:
				break
		else:
			raise Exception('no total line found')

	def getCols(self):
		return [
			'year',
			'superSectionName','superSectionCode',
			'sectionName','sectionCode',
			'categoryName','categoryCode',
			'typeName','typeCode',
			'yAmount','ysAmount','yssAmount','yssccAmount','ysscctAmount',
		]

def writeMoveTable(outputFilename,rows):
	with open(outputFilename,'w',newline='',encoding='utf8') as file:
		writer=csv.writer(file,quoting=csv.QUOTE_NONNUMERIC)
		writer.writerow(['year','departmentName','sectionCode','categoryCode','typeCode'])
		for row in rows:
			writer.writerow(row)

class InvestmentTableWriter:
	def __init__(self,tableReader,years):
		self.rows=[]
		self.levelCols=[
			['grandTotal'],
			['departmentName','departmentTotal'],
			['branchName','branchTotal'],
			['recipientName','recipientTotal'],
			['projectName','districtNames','projectFirstYear','projectLastYear','projectDurationTotal','amount'],
		]
		yearRangeRe=re.compile(r'(\d{4})\s*-\s*(\d{4})')
		rows=[{'year':year} for year in years]
		def fixCase(s):
			s=s.replace('САНКТ-ПЕТЕРБУРГСКОМУ ГОСУДАРСТВЕННОМУ УНИТАРНОМУ ПРЕДПРИЯТИЮ ','СПБ ГУП ')
			s=s.replace('ОТКРЫТОМУ АКЦИОНЕРНОМУ ОБЩЕСТВУ ','ОАО ')
			return s
		def setLevel(toLevel):
			for level,cols in enumerate(self.levelCols):
				if toLevel<level:
					for col in cols:
						for row in rows:
							row.pop(col,None)
		def makeDecimal(v):
			return decimal.Decimal(v).quantize(decimal.Decimal('0.0'))
		def setColValue(k,v):
			for row in rows:
				row[k]=v
		for name,districtNames,yearRange,projectDurationTotal,*amounts in tableReader():
			def setColAmounts(k):
				for row,v in zip(rows,amounts):
					row[k]=makeDecimal(v)
			prefix='ВСЕГО:'
			if name.startswith(prefix):
				setLevel(0)
				setColAmounts('grandTotal')
				continue
			prefix='ЗАКАЗЧИК: '
			if name.startswith(prefix):
				departmentName=name[len(prefix):]
				setLevel(1)
				setColValue('departmentName',departmentName)
				setColAmounts('departmentTotal')
				continue
			prefix='ОТРАСЛЬ: '
			if name.startswith(prefix):
				branchName=name[len(prefix):]
				setLevel(2)
				setColValue('branchName',branchName)
				setColAmounts('branchTotal')
				continue
			prefix='БЮДЖЕТНЫЕ ИНВЕСТИЦИИ '
			if name.startswith(prefix):
				recipientName=fixCase(name[len(prefix):])
				setLevel(3)
				setColValue('recipientName',recipientName)
				setColAmounts('recipientTotal')
				continue
			setLevel(4)
			setColValue('projectName',name)
			setColValue('districtNames',districtNames)
			m=yearRangeRe.match(str(yearRange))
			if m:
				projectFirstYear=int(m.group(1))
				projectLastYear=int(m.group(2))
			elif yearRange is None or yearRange=='':
				projectFirstYear=projectLastYear=None
			else:
				projectFirstYear=projectLastYear=int(yearRange)
			setColValue('projectFirstYear',projectFirstYear)
			setColValue('projectLastYear',projectLastYear)
			if projectDurationTotal:
				setColValue('projectDurationTotal',makeDecimal(projectDurationTotal))
			setColAmounts('amount')
			for row in rows:
				self.rows.append(row.copy())
	def write(self,outputFilename):
		cols=['year']+[col for cols in self.levelCols for col in cols]
		with open(outputFilename,'w',newline='',encoding='utf8') as file:
			writer=csv.writer(file,quoting=csv.QUOTE_NONNUMERIC)
			writer.writerow(cols)
			for row in self.rows:
				writer.writerow([row.get(col) for col in cols])
