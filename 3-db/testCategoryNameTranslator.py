#!/usr/bin/env python3

import unittest

import translators

class TestCategoryNameTranslator(unittest.TestCase):
	def testNoTranslation(self):
		t=translators.CategoryNameTranslator(['foo','bar'])
		tr=t.translateWithReport('baz')
		self.assertFalse(tr.changed)
		self.assertFalse(tr.didQuotes)
		self.assertFalse(tr.didManual)
		self.assertEqual(tr.oldName,'baz')
		self.assertEqual(tr.newName,'baz')
	def testManualTranslation(self):
		t=translators.CategoryNameTranslator(['foo','bar'])
		tr=t.translateWithReport('foo')
		self.assertTrue(tr.changed)
		self.assertFalse(tr.didQuotes)
		self.assertTrue(tr.didManual)
		self.assertEqual(tr.oldName,'foo')
		self.assertEqual(tr.newName,'bar')
	def testQuoteTranslation(self):
		n1='Расходы на содержание Санкт-Петербургского государственного казенного учреждения "Многофункциональный центр предоставления государственных и муниципальных услуг"'
		n2='Расходы на содержание Санкт-Петербургского государственного казенного учреждения «Многофункциональный центр предоставления государственных и муниципальных услуг»'
		t=translators.CategoryNameTranslator()
		tr=t.translateWithReport(n1)
		self.assertTrue(tr.changed)
		self.assertTrue(tr.didQuotes)
		self.assertFalse(tr.didManual)
		self.assertEqual(tr.oldName,n1)
		self.assertEqual(tr.newName,n2)
		# tricky quotes:
		# twice
		# 'Бюджетные инвестиции ОАО "Западный скоростной диаметр" в рамках обеспечения создания автомобильной дороги "Западный скоростной диаметр" за счет средств федерального бюджета'
		# two opening, one closing
		# 'Расходы на предоставление ежемесячных социальных выплат в соответствии с Законом Санкт-Петербурга "О звании "Почетный гражданин Санкт-Петербурга"'
		# both
		# 'Бюджетные инвестиции на увеличение уставного капитала ОАО "Западный скоростной диаметр" в рамках реализации ДЦП СПб "Финансирование создания в Санкт-Петербурге автомобильной дороги "Западный скоростной диаметр"'

if __name__=='__main__':
	unittest.main()
