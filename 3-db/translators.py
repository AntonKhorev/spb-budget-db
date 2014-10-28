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

	def translateWithReport(self,name):
		tr=CategoryNameTranslationReport()
		tr.didQuotes=tr.didManual=False
		tr.oldName=name

		# quote translation
		if name.count('"')==2:
			name,nSubs=re.subn(r'(^|\s)"\b(.*?)\b"(\s|$)',r'\1«\2»\3',name)
			tr.didQuotes=nSubs>0

		# manual translation
		if name in self.translations:
			tr.didManual=True
			name=self.translations[name]

		tr.newName=name
		tr.changed=tr.newName!=tr.oldName
		return tr
