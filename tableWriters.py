#!/usr/bin/env python3

import decimal
import re
import csv

class TableWriter:
	punctWithoutSpaceRe=re.compile(r'(?<=[.,])(?=[^\W\d_])')
	def __init__(self,inputRows,years):
		self.outputRows=outputRows=[]
		levelCols=self.listLevelCols()
		class CurrentRows:
			def __init__(self):
				self.rows=[{'year':year} for year in years]
			def __iter__(self):
				return iter(self.rows)
			def setLevel(self,toLevel):
				for level,cols in enumerate(levelCols):
					if toLevel<=level:
						for col in cols:
							for row in self.rows:
								row.pop(col,None)
			def assignSame(self,k,v):
				for row in self.rows:
					row[k]=v
			def assignDifferent(self,k,vs):
				for row,v in zip(self.rows,vs):
					row[k]=v
			def store(self):
				for row in self.rows:
					outputRows.append(row.copy())
		self.readRows(inputRows,CurrentRows())
	def write(self,outputFilename):
		cols=['year']+[col for cols in self.listLevelCols() for col in cols]
		with open(outputFilename,'w',newline='',encoding='utf8') as file:
			writer=csv.writer(file,quoting=csv.QUOTE_NONNUMERIC)
			writer.writerow(cols)
			for row in self.outputRows:
				writer.writerow([row.get(col) for col in cols])
	def processName(self,name):
		name=' '.join(name.split())
		name=self.punctWithoutSpaceRe.sub(' ',name)
		return name
	def processAmount(self,amount):
		return decimal.Decimal(amount).quantize(decimal.Decimal('0.0'))
	def processAmounts(self,amounts):
		return [self.processAmount(amount) for amount in amounts]
	def listLevelCols(self):
		raise NotImplementedError
	def readRows(self,inputRows,currentRows):
		raise NotImplementedError

class SCTTableWriter(TableWriter):
	def readRows(self,inputRows,currentRows):
		class GrandTotalBox:
			def set(self,value):
				self.value=value
			def __str__(self):
				return str(self.value)
		grandTotalBoxes=[GrandTotalBox() for row in currentRows]
		currentRows.assignDifferent('grandTotal',grandTotalBoxes)
		def setGrandTotals(amounts):
			for amount,box in zip(amounts,grandTotalBoxes):
				box.set(amount)
		self.readRowsWithGrandTotalsDeferred(inputRows,currentRows,setGrandTotals)
	def readRowsWithGrandTotalsDeferred(self,inputRows,currentRows,setGrandTotals):
		raise NotImplementedError

class DepartmentTableWriter(SCTTableWriter):
	def listLevelCols(self):
		return [
			['grandTotal'],
			['departmentName','departmentCode','departmentTotal'],
			['sectionCode','categoryName','categoryCode','categoryTotal'],
			['typeName','typeCode','amount'],
		]
	def readRowsWithGrandTotalsDeferred(self,inputRows,currentRows,setGrandTotals):
		departmentNameRe=re.compile(r'(?P<departmentName>.*?)\s*\((?P<departmentCode>...)\)')
		for number,name,sectionCode,categoryCode,typeCode,*amounts in inputRows:
			amounts=self.processAmounts(amounts)
			name=self.processName(name)
			sectionCode=sectionCode[:2]+sectionCode[-2:]
			typeCode=str(typeCode)
			if not number:
				setGrandTotals(amounts)
				break
			elif not sectionCode:
				m=departmentNameRe.match(name)
				currentRows.setLevel(1)
				currentRows.assignSame('departmentName',m.group('departmentName'))
				currentRows.assignSame('departmentCode',m.group('departmentCode'))
				currentRows.assignDifferent('departmentTotal',amounts)
			elif not typeCode:
				currentRows.setLevel(2)
				currentRows.assignSame('sectionCode',sectionCode)
				currentRows.assignSame('categoryName',name)
				currentRows.assignSame('categoryCode',categoryCode)
				currentRows.assignDifferent('categoryTotal',amounts)
			else:
				currentRows.setLevel(3)
				currentRows.assignSame('typeName',name)
				currentRows.assignSame('typeCode',typeCode)
				currentRows.assignDifferent('amount',amounts)
				currentRows.store()
		else:
			raise Exception('no total line found')

class SectionTableWriter(SCTTableWriter):
	def listLevelCols(self):
		return [
			['grandTotal'],
			['superSectionName','superSectionCode','superSectionTotal'],
			['sectionName','sectionCode','sectionTotal'],
			['categoryName','categoryCode','categoryTotal'],
			['typeName','typeCode','amount'],
		]
	def readRowsWithGrandTotalsDeferred(self,inputRows,currentRows,setGrandTotals):
		for number,name,sectionCode,categoryCode,typeCode,*amounts in inputRows:
			amounts=self.processAmounts(amounts)
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
			if not number:
				setGrandTotals(amounts)
				break
			elif not sectionCode:
				currentRows.setLevel(1)
				currentRows.assignSame('superSectionName',name)
				currentRows.assignSame('superSectionCode',superSectionCode)
				currentRows.assignDifferent('superSectionTotal',amounts)
			elif not categoryCode:
				currentRows.setLevel(2)
				currentRows.assignSame('sectionName',name)
				currentRows.assignSame('sectionCode',sectionCode)
				currentRows.assignDifferent('sectionTotal',amounts)
			elif not typeCode:
				currentRows.setLevel(3)
				currentRows.assignSame('categoryName',name)
				currentRows.assignSame('categoryCode',categoryCode)
				currentRows.assignDifferent('categoryTotal',amounts)
			else:
				currentRows.setLevel(4)
				currentRows.assignSame('typeName',name)
				currentRows.assignSame('typeCode',typeCode)
				currentRows.assignDifferent('amount',amounts)
				currentRows.store()
		else:
			raise Exception('no total line found')

class InvestmentTableWriter(TableWriter):
	def listLevelCols(self):
		return [
			['grandTotal'],
			['departmentName','departmentTotal'],
			['branchName','branchTotal'],
			['recipientName','recipientTotal'],
			['projectName','districtNames','projectFirstYear','projectLastYear','projectDurationTotal','amount'],
		]
	def readRows(self,inputRows,currentRows):
		yearRangeRe=re.compile(r'(\d{4})\s*-\s*(\d{4})')
		def fixCase(s):
			s=s.replace('САНКТ-ПЕТЕРБУРГСКОМУ ГОСУДАРСТВЕННОМУ УНИТАРНОМУ ПРЕДПРИЯТИЮ ','СПБ ГУП ')
			s=s.replace('ОТКРЫТОМУ АКЦИОНЕРНОМУ ОБЩЕСТВУ ','ОАО ')
			return s
		for name,districtNames,yearRange,projectDurationTotal,*amounts in inputRows:
			amounts=self.processAmounts(amounts)
			# name=self.processName(name)
			prefix='ВСЕГО:'
			if name.startswith(prefix):
				currentRows.setLevel(0)
				currentRows.assignDifferent('grandTotal',amounts)
				continue
			prefix='ЗАКАЗЧИК: '
			if name.startswith(prefix):
				departmentName=name[len(prefix):]
				currentRows.setLevel(1)
				currentRows.assignSame('departmentName',departmentName)
				currentRows.assignDifferent('departmentTotal',amounts)
				continue
			prefix='ОТРАСЛЬ: '
			if name.startswith(prefix):
				branchName=name[len(prefix):]
				currentRows.setLevel(2)
				currentRows.assignSame('branchName',branchName)
				currentRows.assignDifferent('branchTotal',amounts)
				continue
			prefix='БЮДЖЕТНЫЕ ИНВЕСТИЦИИ '
			if name.startswith(prefix):
				recipientName=fixCase(name[len(prefix):])
				currentRows.setLevel(3)
				currentRows.assignSame('recipientName',recipientName)
				currentRows.assignDifferent('recipientTotal',amounts)
				continue
			currentRows.setLevel(4)
			currentRows.assignSame('projectName',name)
			currentRows.assignSame('districtNames',districtNames)
			m=yearRangeRe.match(str(yearRange))
			if m:
				projectFirstYear=int(m.group(1))
				projectLastYear=int(m.group(2))
			elif yearRange is None or yearRange=='':
				projectFirstYear=projectLastYear=None
			else:
				projectFirstYear=projectLastYear=int(yearRange)
			currentRows.assignSame('projectFirstYear',projectFirstYear)
			currentRows.assignSame('projectLastYear',projectLastYear)
			if projectDurationTotal:
				currentRows.assignSame('projectDurationTotal',self.processAmount(projectDurationTotal))
			currentRows.assignDifferent('amount',amounts)
			currentRows.store()

def writeMoveTable(outputFilename,rows):
	with open(outputFilename,'w',newline='',encoding='utf8') as file:
		writer=csv.writer(file,quoting=csv.QUOTE_NONNUMERIC)
		writer.writerow(['year','departmentName','sectionCode','categoryCode','typeCode'])
		for row in rows:
			writer.writerow(row)
