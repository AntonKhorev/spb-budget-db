import sqlite3

class Conn:
	# table name : join key column name -> JOIN table USING(column)
	tables={
		# 'items':None,
		'edits':'editNumber',
		'departments':'departmentCode',
		'sections':'sectionCode',
		'superSections':'superSectionCode',
		'categories':'categoryCode',
		'types':'typeCode',
	}
	entries={
		'editNumber':'items',
		'year':'items',
		'departmentCode':'items',
		'sectionCode':'items',
		'categoryCode':'items',
		'typeCode':'items',
		'documentNumber':'edits',
		'paragraphNumber':'edits',
		'departmentName':'departments',
		'departmentOrder':'departments',
		'superSectionCode':'sections',
		'sectionName':'sections',
		'superSectionName':'superSections',
		'categoryName':'categories',
		'typeName':'types',
	}
	def execute(self,query):
		raise NotImplementedError
	def queryAmounts(self,keys):
		qg=','.join(keys)
		q='SELECT '+qg+',SUM(amount) AS amount\n'
		q+='FROM items\n'
		froms={'items'}
		def rec(key):
			nonlocal q
			if key not in self.entries:
				raise ValueError('unknown db table column "'+key+'"')
			table=self.entries[key]
			if table in froms or table not in self.tables:
				return
			joinKey=self.tables[table]
			rec(joinKey)
			q+='JOIN '+table+' USING('+joinKey+')\n'
		for key in keys:
			rec(key)
		q+='GROUP BY '+qg
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
