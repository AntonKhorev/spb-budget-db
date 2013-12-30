import collections
import csv

class DepartmentFixer: # also InvestmentFixer
	def __init__(self,csvFilename):
		# documentNumber -> paragraphNumber -> s -> t
		self.allFixes=collections.defaultdict(lambda: collections.defaultdict(dict))
		with open(csvFilename,encoding='utf8',newline='') as csvFile:
			reader=csv.reader(csvFile)
			next(reader) # skip header
			for s,t in zip(reader,reader):
				self.allFixes[s[0]][s[1]+'.'][tuple(s[2:])]=t[2:]
	def fixTableReader(self,documentNumber,paragraphNumber,tableReader):
		fixes=self.allFixes[documentNumber][paragraphNumber]
		return lambda: (fixes.get(tuple(row),row) for row in tableReader())

departmentFixer=DepartmentFixer('2014.0.p.errors.csv')
