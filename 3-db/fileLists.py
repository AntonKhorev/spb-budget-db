import re

class AbstractAction:
	pass

class SetAction(AbstractAction):
	def __init__(self,fiscalYears):
		self.fiscalYears=set(fiscalYears)

class DiffAction(AbstractAction):
	pass

class DiffsetAction(AbstractAction):
	def __init__(self,documentNumber,fiscalYears):
		self.documentNumber=documentNumber
		self.fiscalYears=set(fiscalYears)

class MoveAction(AbstractAction):
	pass

class TableFile:
	def __init__(self,filename,stageYear,documentNumber,paragraphNumber,table,action):
		self.filename=filename
		self.stageYear=stageYear
		self.documentNumber=documentNumber
		self.paragraphNumber=paragraphNumber
		self.table=table
		self.action=action

# sort by document and paragraph number
# use with filenames=glob.glob('dir/*.csv')
def listTableFiles(filenames):
	r=re.compile(r'^(?:.+[/\\])?(?P<stageYear>\d+)\.(?P<documentNumber>\d+)\.(?P<paragraphNumber>\d+(?:\.\d+)*)\.(?P<table>[a-z]+)\.(?P<action>[a-z0-9(),]+)\.csv$')
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
			args=[int(arg) for arg in actText[4:-1].split(',')]
			action=SetAction(args)
		elif actText.startswith('diffset('):
			args=[int(arg) for arg in actText[8:-1].split(',')]
			action=DiffsetAction(args[0],args[1:])
		else:
			raise Exception('invalid action '+actText)
		tableFile=TableFile(filename,int(m.group('stageYear')),int(m.group('documentNumber')),m.group('paragraphNumber'),m.group('table'),action)
		tableFiles.append(tableFile)
	def sortKey(tableFile):
		return (tableFile.stageYear,tableFile.documentNumber)+tuple(int(n) for n in tableFile.paragraphNumber.split('.'))
	tableFiles.sort(key=sortKey)
	return tableFiles
