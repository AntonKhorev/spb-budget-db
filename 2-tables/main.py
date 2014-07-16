#!/usr/bin/env python3

outputDirectory='../2-tables.out'
outputContentDirectory=outputDirectory+'/content'
import os,shutil
if not os.path.exists(outputContentDirectory):
	os.makedirs(outputContentDirectory)
for filename in os.listdir('content'):
	shutil.copy(
		os.path.join('content',filename),
		outputContentDirectory
	)

import makeTablesFromCsv
import makeTablesFromOdf
import makeTablesFromXlsx

# currently broken and not used:
# import makeInvestmentTablesFromXlsx
