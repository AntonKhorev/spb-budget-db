#!/usr/bin/env python3

import re
import csv

class TableWriter:
	def __init__(self,tableReader,amendmentNumber,years):
		self.amendmentNumber=amendmentNumber
		self.years=years
		self.rows=[{}]*len(years) # reserve first rows for totals
		self.punctWithoutSpaceRe=re.compile(r'(?<=[.,])(?=[^\W\d_])')
		self.processTable(tableReader(years))

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
		writer.writerow(['amendmentNumber']+cols)
		for row in self.rows:
			writer.writerow([self.amendmentNumber]+[row.get(col) for col in cols])

class DepartmentTableWriter(TableWriter):
	def processTable(self,tableReader):
		departmentNameRe=re.compile(r'(?P<departmentName>.*?)\s*\((?P<departmentCode>...)\)')
		for (number,name,sectionCode,categoryCode,typeCode),amounts in tableReader:
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
		for (number,name,sectionCode,categoryCode,typeCode),amounts in tableReader:
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
