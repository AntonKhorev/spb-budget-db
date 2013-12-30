import collections
import csv

class DepartmentFixer:
	def __init__(self,csvFilename):
		# documentNumber -> paragraphNumber -> number -> (s,t)
		self.allFixes=collections.defaultdict(lambda: collections.defaultdict(dict))
		with open(csvFilename,encoding='utf8',newline='') as csvFile:
			reader=csv.reader(csvFile)
			next(reader) # skip header
			for s,t in zip(reader,reader):
				# print('read fix for',s[0],s[1],s[2])
				self.allFixes[s[0]][s[1]+'.'][s[2]]=(s[3:],t[3:])
	def fixTableReader(self,documentNumber,paragraphNumber,tableReader):
		fixes=self.allFixes[documentNumber][paragraphNumber]
		# print('fixer for',documentNumber,paragraphNumber,'with fixes',fixes)
		def fixedReader():
			for row in tableReader():
				# print('got',row)
				number=row[0]
				rest=row[1:]
				if number in fixes:
					s,t=fixes[number]
					if s!=rest:
						raise Exception('expected department table error not found')
					# print('fixed',documentNumber,paragraphNumber,number)
					yield [number]+t
				else:
					# print('skipped',documentNumber,paragraphNumber,number)
					yield row
		return fixedReader

departmentFixer=DepartmentFixer('2014.0.p.errors.csv')
