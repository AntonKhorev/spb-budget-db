#!/usr/bin/env python3

outputDirectory='../2-tables.out'
import os,shutil
for directory in ('meta','content'):
	outputSubDirectory=os.path.join(outputDirectory,directory)
	if not os.path.exists(outputSubDirectory):
		os.makedirs(outputSubDirectory)
	for filename in os.listdir(directory):
		shutil.copy(
			os.path.join(directory,filename),
			outputSubDirectory
		)

import makeTablesFromCsv
import makeTablesFromOdf
import makeTablesFromXlsx

# currently broken and not used:
# import makeInvestmentTablesFromXlsx
