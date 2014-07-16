#!/usr/bin/env python3

outputDirectory='../2-tables.out'
import os
if not os.path.exists(outputDirectory):
	os.makedirs(outputDirectory)

import makeTablesByHand
import makeTablesFromCsv
import makeTablesFromOdf
import makeTablesFromXlsx

# currently broken and not used:
# import makeInvestmentTablesFromXlsx
