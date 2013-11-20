import ezodf
doc=ezodf.opendoc('assembly/3765.odt')
for obj in doc.body:
	if type(obj) is ezodf.text.Paragraph:
		print('text paragraph {',obj.plaintext(),'}')
	elif type(obj) is ezodf.table.Table:
		print('table',obj.nrows(),'x',obj.ncols())
	else:
		print('something else',obj)
