import re

class CategoryNameTranslationReport:
	def __str__(self):
		m=[]
		if self.didQuotes: m.append('quotes')
		if self.didDashes: m.append('dashes')
		if self.didManual: m.append('manual')
		return 'category name translation using ('+','.join(m)+') from ('+self.oldName+') to ('+self.newName+')'

class CategoryNameTranslator:
	def __init__(self,lines=[]):
		# category name translations between years
		# lines = list of old name, new name, old name, new name, ...
		lines=(re.sub(' +',' ',line.strip()) for line in lines)
		self.translations={s:t for s,t in zip(lines,lines)}
		self.unusedManualTranslations=set(self.translations.keys())

	def translateWithReport(self,name):
		tr=CategoryNameTranslationReport()
		tr.didQuotes=tr.didDashes=tr.didManual=False
		tr.oldName=name

		# quote translation
		qPre=r'(^|\s)'
		qPost=r'(\W|$)'
		qIn=r'([^"]*)'
		qO='["«]'
		qC='["»]'
		nQuotes=sum(c in '"«»' for c in name)
		if nQuotes==2:
			# ... "..." ...
			name,nSubs=re.subn(qPre+qO+r'\b'+qIn+r'\b'+qC+qPost,r'\1«\2»\3',name)
			tr.didQuotes=nSubs>0
		elif nQuotes==3:
			# ... "... "..." ...
			name,nSubs=re.subn(qPre+qO+r'\b'+qIn+r'\s'+qO+qIn+r'\b'+qC+qPost,r'\1«\2 „\3“»\4',name)
			tr.didQuotes=nSubs>0
		elif nQuotes==4:
			if True:
				# ... "... "..." ..." ...
				name,nSubs=re.subn(qPre+qO+r'\b'+qIn+r'\s'+qO+r'\b'+qIn+r'\b'+qC+r'\s'+qIn+r'\b'+qC+qPost,r'\1«\2 „\3“ \4»\5',name)
				tr.didQuotes=nSubs>0
			if not tr.didQuotes:
				# ... "..." ... "..." ...
				name,nSubs=re.subn(qPre+qO+r'\b'+qIn+r'\b'+qC+qPost+qIn+qPre+qO+r'\b'+qIn+r'\b'+qC+qPost,r'\1«\2»\3\4\5«\6»\7',name)
				tr.didQuotes=nSubs>0

		# dash translation
		name,nSubs=re.subn('\s[-–—]\s',' — ',name)
		tr.didDashes=nSubs>0

		# manual translation
		if name in self.translations:
			self.unusedManualTranslations.discard(name)
			tr.didManual=True
			name=self.translations[name]

		tr.newName=name
		tr.changed=tr.newName!=tr.oldName
		return tr

	def getUnusedManualTranslations(self):
		return self.unusedManualTranslations
