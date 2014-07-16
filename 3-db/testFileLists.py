#!/usr/bin/env python3

import unittest

import fileLists

class TestFileLists(unittest.TestCase):
	def testOneEntry(self):
		l=fileLists.listTableFiles([
			'2014.3765.1.1.department.diff.csv',
		])
		self.assertEqual(len(l),1)
		t=l[0]
		self.assertEqual(t.year,2014)
		self.assertEqual(t.documentNumber,3765)
		self.assertEqual(t.paragraphNumber,'1.1')
		self.assertEqual(t.table,'department')
		self.assertIsInstance(t.action,fileLists.DiffAction)
	def testOneEntryWithDirectory(self):
		l=fileLists.listTableFiles([
			'tables\\2014.3574.3.department.set(2014).csv'
		])
		self.assertEqual(len(l),1)
	def testSort(self):
		l=fileLists.listTableFiles([
			'2014.3765.7.1.department.diff.csv',
			'2014.3765.10.4.department.diff.csv',
			'2014.3765.1.1.department.diff.csv',
		])
		self.assertEqual(len(l),3)
		self.assertEqual(l[0].paragraphNumber,'1.1')
		self.assertEqual(l[1].paragraphNumber,'7.1')
		self.assertEqual(l[2].paragraphNumber,'10.4')
	def testSet(self):
		l=fileLists.listTableFiles([
			'2014.3765.1.1.department.set(2015,2016).csv',
		])
		self.assertEqual(len(l),1)
		self.assertIsInstance(l[0].action,fileLists.SetAction)
		self.assertEqual(l[0].action.years,{2015,2016})
	def testDiffset(self):
		l=fileLists.listTableFiles([
			'2014.3765.1.1.department.diffset(1234,2015,2016).csv',
		])
		self.assertEqual(len(l),1)
		self.assertIsInstance(l[0].action,fileLists.DiffsetAction)
		self.assertEqual(l[0].action.documentNumber,1234)
		self.assertEqual(l[0].action.years,{2015,2016})

if __name__=='__main__':
	unittest.main()
