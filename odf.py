#!/usr/bin/env python3

import re
import ezodf

paragraphRe=re.compile(r'Пункт N (?P<paragraphNumber>\d+(?:\.\d+)*)')
amendTextRe=re.compile(r'(?P<paragraphNumber>(?:\d+\.)+) В текстовую часть')
amendAppendixRe=re.compile(r'(?P<paragraphNumber>(?:\d+\.)+) В приложение (?P<appendixNumber>\d+)')

doc=ezodf.opendoc('assembly/3765.odt')
for obj in doc.body:
	if type(obj) is ezodf.text.Paragraph:
		print('text paragraph {')
		for line in obj.plaintext().splitlines():
			m=paragraphRe.match(line)
			if m:
				print('=== paragraph',m.group('paragraphNumber'),'===')
			m=amendTextRe.match(line)
			if m:
				print('=== amendment',m.group('paragraphNumber'),'for text ===')
			m=amendAppendixRe.match(line)
			if m:
				print('=== amendment',m.group('paragraphNumber'),'for appendix',m.group('appendixNumber'),'===')
				if m.group('appendixNumber') in ('3','4'):
					print('===*** got to process it ***===')
			print('text line:',line)
		print('}')
	elif type(obj) is ezodf.table.Table:
		print('table',obj.nrows(),'x',obj.ncols())
