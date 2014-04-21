import re

class AbstractAction:
	pass

class DiffAction(AbstractAction):
	pass

class MoveAction(AbstractAction):
	pass

class SetAction(AbstractAction):
	def __init__(self,years):
		self.years=set(years)

class TableFile:
	def __init__(self,filename,stage,documentNumber,paragraphNumber,table,action):
		self.filename=filename
		self.stage=stage
		self.documentNumber=documentNumber
		self.paragraphNumber=paragraphNumber
		self.table=table
		self.action=action

# sort by document and paragraph number
def listTableFiles(filenames):
	r=re.compile(r'^(?:.+[/\\])?(?P<stage>\d+\.\d\.[pz])\.(?P<documentNumber>\d+)\.(?P<paragraphNumber>\d[0-9.]+)\.(?P<table>[a-z]+)\.(?P<action>[a-z0-9(),]+)\.csv$')
	tableFiles=[]
	for filename in filenames:
		m=r.match(filename)
		if not m: continue
		actText=m.group('action')
		if actText=='diff':
			action=DiffAction()
		elif actText=='move':
			action=MoveAction()
		elif actText.startswith('set('):
			action=SetAction([int(year) for year in actText[4:-1].split(',')])
		else:
			raise Exception('invalid action '+actText)
		tableFile=TableFile(filename,m.group('stage'),int(m.group('documentNumber')),m.group('paragraphNumber'),m.group('table'),action)
		tableFiles.append(tableFile)
	def sortKey(tableFile):
		return (tableFile.stage,tableFile.documentNumber)+tuple(int(n) for n in tableFile.paragraphNumber.split('.'))
	tableFiles.sort(key=sortKey)
	return tableFiles
