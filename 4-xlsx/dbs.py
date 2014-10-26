import sqlite3

class Conn:
	# TODO turn into template w/ documentNumber argument
	categoriesSubquery="""(
		SELECT categories.categoryId,categoryCode,categoryName
		FROM categories
		LEFT JOIN documentCategoryCodes ON categories.categoryId=documentCategoryCodes.categoryId AND documentNumber=5208
	)"""
	# table name : join key column names -> [LEFT] JOIN table USING(column1,column2,...)
	tables={
		# 'items':None,
		'edits':['editNumber'],
		'documents':['documentNumber'],
		'authors':['authorId'],
		'stages':['stageYear','stageNumber'],
		'departments':['departmentCode'],
		'sections':['sectionCode'],
		'superSections':['superSectionCode'],
		categoriesSubquery:['categoryId'],
		'types':['typeCode'],
	}
	# column name : table to join starting from items
	entries={
		'stageAssemblyUrl':'stages',
		'authorShortName':'authors',
		'authorLongName':'authors',
		'documentDate':'documents',
		'stageYear':'documents',
		'stageNumber':'documents',
		'amendmentFlag':'documents',
		'authorId':'documents',
		'documentAssemblyUrl':'documents',
		'documentNumber':'edits',
		'paragraphNumber':'edits',
		'departmentName':'departments',
		'departmentOrder':'departments',
		'superSectionCode':'sections',
		'sectionName':'sections',
		'superSectionName':'superSections',
		'categoryCode':categoriesSubquery,
		'categoryName':categoriesSubquery,
		'typeName':'types',
		'editNumber':'items',
		'fiscalYear':'items',
		'departmentCode':'items',
		'sectionCode':'items',
		'categoryId':'items',
		'typeCode':'items',
	}
	def execute(self,query):
		raise NotImplementedError
	def buildFroms(self,keys):
		froms={'items'}
		q='FROM items\n'
		def rec(key):
			nonlocal q
			if key not in self.entries:
				raise ValueError('unknown db table column "'+key+'"')
			table=self.entries[key]
			if table in froms or table not in self.tables:
				return
			joinKeys=self.tables[table]
			for joinKey in joinKeys:
				rec(joinKey)
			froms.add(table)
			q+='LEFT JOIN '+table+' USING('+','.join(joinKeys)+')\n' # need LEFT JOIN for queries with author names
		for key in keys:
			rec(key)
		return q
	def queryAmounts(self,keys):
		qg=','.join(keys)
		q='SELECT '+qg+',SUM(amount) AS amount\n'
		q+=self.buildFroms(keys)
		q+='GROUP BY '+qg+'\n'
		print(q) ##
		return self.execute(q)
	def queryHeaders(self,selects,orderbys):
		q='SELECT DISTINCT '+','.join(selects)+'\n'
		q+=self.buildFroms(selects+orderbys)
		q+='ORDER BY '+','.join(orderbys)+'\n'
		print(q) ##
		return self.execute(q)

class Sqlite:
	def __init__(self,filename):
		self.filename=filename
	def __enter__(self):
		self.conn=sqlite3.connect(':memory:')
		self.conn.row_factory=sqlite3.Row
		self.conn.execute('pragma foreign_keys=ON')
		with open(self.filename,encoding='utf8') as script:
			self.conn.executescript(script.read())
		class SqliteConn(Conn):
			def __init__(self,conn):
				self.conn=conn
			def execute(self,query):
				return self.conn.execute(query)
		return SqliteConn(self.conn)
	def __exit__(self,type,value,tb):
		self.conn.close()
