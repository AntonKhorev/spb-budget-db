import re

class CategoryNameTranslationReport:
	def __str__(self):
		m=[]
		if self.didQuotes: m.append('quotes')
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
		tr.didQuotes=tr.didManual=False
		tr.oldName=name

		# quote translation
		qPre=r'(^|\s)'
		qPost=r'(\W|$)'
		qIn=r'([^"]*)'
		if name.count('"')==2:
			# ... "..." ...
			name,nSubs=re.subn(qPre+r'"\b'+qIn+r'\b"'+qPost,r'\1«\2»\3',name)
			tr.didQuotes=nSubs>0
		elif name.count('"')==4:
			if True:
				# ... "... "..." ..." ...
				name,nSubs=re.subn(qPre+r'"\b'+qIn+r'\s"\b'+qIn+r'\b"\s'+qIn+r'\b"'+qPost,r'\1«\2 «\3» \4»\5',name)
				tr.didQuotes=nSubs>0
			if not tr.didQuotes:
				# ... "..." ... "..." ...
				name,nSubs=re.subn(qPre+r'"\b'+qIn+r'\b"'+qPost+qIn+qPre+r'"\b'+qIn+r'\b"'+qPost,r'\1«\2»\3\4\5«\6»\7',name)
				tr.didQuotes=nSubs>0
		elif name.count('«')==1 and name.count('"')==1:
			# ... «..." ...
			name,nSubs=re.subn(qPre+r'«\b'+qIn+r'\b"'+qPost,r'\1«\2»\3',name)
			tr.didQuotes=nSubs>0

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
