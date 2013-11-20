#!/usr/bin/env python3

import re
import ezodf

paragraphRe=re.compile(r'Пункт N (?P<paragraphNumber>\d+(?:\.\d+)*)')

doc=ezodf.opendoc('assembly/3765.odt')
for obj in doc.body:
	if type(obj) is ezodf.text.Paragraph:
		print('text paragraph {')
		for line in obj.plaintext().splitlines():
			m=paragraphRe.match(line)
			if m:
				print('=== paragraph',m.group('paragraphNumber'),'===')
			print('text line:',line)
		print('}')
	elif type(obj) is ezodf.table.Table:
		print('table',obj.nrows(),'x',obj.ncols())
