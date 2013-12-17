import itertools

class Lines:
	BEFORE=1
	AFTER=2
	def listEntries(self):
		raise NotImplementedError
	def listKeyEntries(self):
		raise NotImplementedError
	def listLevelOrders(self):
		# order for final level should be BEFORE
		raise NotImplementedError
	def listItemLevelKeys(self,item):
		raise NotImplementedError
	def getItemValues(self,item,level):
		raise NotImplementedError
	def buildSqlQuery(self,where):
		raise NotImplementedError
	def getData(self,sqlConn):
		# TODO store/return key->line# map
		levelOrders=self.listLevelOrders()
		noneKeys=[None for _ in levelOrders]
		oldItem=None
		oldLevelKeys=noneKeys
		for item in itertools.chain(
			sqlConn.execute(self.buildSqlQuery("1")),
			(None,)
		):
			if item is None:
				levelKeys=noneKeys
			else:
				levelKeys=self.listItemLevelKeys(item)
			reset=False
			for level,levelKey in enumerate(levelKeys):
				if reset or levelKey!=oldLevelKeys[level]:
					reset=True
					if levelOrders[level]==self.BEFORE and item is not None:
						yield level,self.getItemValues(item,level)
					elif levelOrders[level]==self.AFTER and oldItem is not None:
						yield level,self.getItemValues(oldItem,level)
			oldItem=item
			oldLevelKeys=levelKeys

class DepartmentRows(Lines):
	def listEntries(self):
		return [
			'name',
			'departmentCode',
			'sectionCode',
			'categoryCode',
			'typeCode',
		]
	def listKeyEntries(self):
		return [
			'departmentCode',
			'sectionCode',
			'categoryCode',
			'typeCode',
		]
	def listLevelOrders(self):
		return [
			self.AFTER,
			self.BEFORE,
			self.BEFORE,
			self.BEFORE,
		]
	def listItemLevelKeys(self,item):
		return [
			tuple(),
			(item['departmentCode'],),
			(item['departmentCode'],item['sectionCode'],item['categoryCode']),
			(item['departmentCode'],item['sectionCode'],item['categoryCode'],item['typeCode']),
		]
	def getItemValues(self,item,level):
		if level==0:
			return ('Итого',)
		elif level==1:
			return (item['departmentName'],item['departmentCode'])
		elif level==2:
			return (item['categoryName'],item['departmentCode'],item['sectionCode'],item['categoryCode'])
		elif level==3:
			return (item['typeName'],item['departmentCode'],item['sectionCode'],item['categoryCode'],item['typeCode'])
		raise ValueError()
	def buildSqlQuery(self,where):
		return """
			SELECT DISTINCT departmentCode,sectionCode,categoryCode,typeCode,
			                departmentName,            categoryName,typeName
			FROM items
			JOIN departments USING(departmentCode)
			JOIN categories USING(categoryCode)
			JOIN types USING(typeCode)
		"""+"WHERE "+where+"""
			ORDER BY departmentOrder,sectionCode,categoryCode,typeCode
		""";

class SectionRows(Lines):
	def listEntries(self):
		return [
			'name',
			'sectionCode',
			'categoryCode',
			'typeCode',
		]
	def listKeyEntries(self):
		return [
			'superSectionCode',
			'sectionCode',
			'categoryCode',
			'typeCode',
		]
	def listLevelOrders(self):
		return [
			self.AFTER,
			self.BEFORE,
			self.BEFORE,
			self.BEFORE,
			self.BEFORE,
		]
	def listItemLevelKeys(self,item):
		return [
			tuple(),
			(item['superSectionCode'],),
			(item['sectionCode'],),
			(item['sectionCode'],item['categoryCode']),
			(item['sectionCode'],item['categoryCode'],item['typeCode']),
		]
	def getItemValues(self,item,level):
		if level==0:
			return ('Итого',)
		elif level==1:
			return (item['superSectionName'],item['superSectionCode'])
		elif level==2:
			return (item['sectionName'],item['sectionCode'])
		elif level==3:
			return (item['categoryName'],item['sectionCode'],item['categoryCode'])
		elif level==4:
			return (item['typeName'],item['sectionCode'],item['categoryCode'],item['typeCode'])
		raise ValueError()
	def buildSqlQuery(self,where):
		return """
			SELECT DISTINCT superSectionCode,sectionCode,categoryCode,typeCode,
			                superSectionName,sectionName,categoryName,typeName
			FROM items
			JOIN sections USING(sectionCode)
			JOIN superSections USING(superSectionCode)
			JOIN categories USING(categoryCode)
			JOIN types USING(typeCode)
		"""+"WHERE "+where+"""
			ORDER BY superSectionCode,sectionCode,categoryCode,typeCode
		""";

class AmendmentCols(Lines):
	def listEntries(self):
		return [
			'year',
			'documentNumber',
		]
	def listKeyEntries(self):
		return self.listEntries()
	def listLevelOrders(self):
		return [
			self.AFTER,
			self.BEFORE,
		]
	def listItemLevelKeys(self,item):
		return [
			(item['year'],),
			(item['year'],item['documentNumber']),
		]
	def getItemValues(self,item,level):
		if level==0:
			return (str(item['year'])+' г.','Итого (тыс. руб.)')
		elif level==1:
			return (str(item['year'])+' г.','Изменения в док. '+str(item['documentNumber'])+ ' (тыс. руб.)')
		raise ValueError()
	def buildSqlQuery(self,where):
		return """
			SELECT DISTINCT year,documentNumber
			FROM items
			JOIN edits USING(editNumber)
		"""+"WHERE "+where+"""
			ORDER BY year,documentNumber
		"""
