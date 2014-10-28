import re

class CategoryNameTranslator:
	def __init__(self,filename):
		with open('categoryNameTranslations.txt',encoding='utf8') as nameFile:
			# category name translations between years
			# file format: old name \n new name \n old name \n new name ...
			# TODO fix typography
			lines=(re.sub(' +',' ',line.strip()) for line in nameFile)
			self.translations={s:t for s,t in zip(lines,lines)}
	def getTranslations(self):
		return self.translations
