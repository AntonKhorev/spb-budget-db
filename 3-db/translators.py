import re

class CategoryNameTranslationReport:
	pass

class CategoryNameTranslator:
	def __init__(self,lines):
		# category name translations between years
		# lines = list of old name, new name, old name, new name, ...
		# TODO fix typography: quotes in (non-word char)"(word char).?*(word char)"(non-word char)
		lines=(re.sub(' +',' ',line.strip()) for line in lines)
		self.translations={s:t for s,t in zip(lines,lines)}
	def translateWithReport(self,name):
		tr=CategoryNameTranslationReport()
		tr.changed=False
		tr.newName=tr.oldName=name
		if name in self.translations:
			tr.changed=True
			tr.newName=self.translations[name]
		return tr
