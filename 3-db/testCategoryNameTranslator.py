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

	def doTestQuoteTranslation(self,n1,n2):
		t=translators.CategoryNameTranslator()
		tr=t.translateWithReport(n1)
		self.assertTrue(tr.changed)
		self.assertTrue(tr.didQuotes)
		self.assertFalse(tr.didManual)
		self.assertEqual(tr.oldName,n1)
		self.assertEqual(tr.newName,n2)
	def testQuoteTranslation(self):
		self.doTestQuoteTranslation(
			'Расходы на содержание Санкт-Петербургского государственного казенного учреждения "Многофункциональный центр предоставления государственных и муниципальных услуг"',
			'Расходы на содержание Санкт-Петербургского государственного казенного учреждения «Многофункциональный центр предоставления государственных и муниципальных услуг»'
		)
	def testNestedQuoteTranslation(self):
		self.doTestQuoteTranslation(
			'Субсидии бюджетному учреждению "Испытательная лаборатория пищевых продуктов и продовольственного сырья "СОЦПИТ" Управления социального питания" на финансовое обеспечение выполнения государственного задания',
			'Субсидии бюджетному учреждению «Испытательная лаборатория пищевых продуктов и продовольственного сырья „СОЦПИТ“ Управления социального питания» на финансовое обеспечение выполнения государственного задания'
		)
	def testNestedQuoteTranslation2(self):
		self.doTestQuoteTranslation(
			'Субсидии бюджетному учреждению «Испытательная лаборатория пищевых продуктов и продовольственного сырья «СОЦПИТ» Управления социального питания» на финансовое обеспечение выполнения государственного задания',
			'Субсидии бюджетному учреждению «Испытательная лаборатория пищевых продуктов и продовольственного сырья „СОЦПИТ“ Управления социального питания» на финансовое обеспечение выполнения государственного задания'
		)
	def testTwoQuoteTranslation(self):
		self.doTestQuoteTranslation(
			'Бюджетные инвестиции ОАО "Западный скоростной диаметр" в рамках обеспечения создания автомобильной дороги "Западный скоростной диаметр" за счет средств федерального бюджета',
			'Бюджетные инвестиции ОАО «Западный скоростной диаметр» в рамках обеспечения создания автомобильной дороги «Западный скоростной диаметр» за счет средств федерального бюджета'
		)
	def testQuoteFollowedByPunctuationTranslation(self):
		self.doTestQuoteTranslation(
			'Расходы на государственную автоматизированную информационную систему "Выборы", повышение правовой культуры избирателей и организаторов выборов',
			'Расходы на государственную автоматизированную информационную систему «Выборы», повышение правовой культуры избирателей и организаторов выборов'
		)
	def testOpenOpenCloseQuoteTranslation(self):
		self.doTestQuoteTranslation(
			'Расходы на предоставление ежемесячных социальных выплат в соответствии с Законом Санкт-Петербурга "О звании "Почетный гражданин Санкт-Петербурга"',
			'Расходы на предоставление ежемесячных социальных выплат в соответствии с Законом Санкт-Петербурга «О звании „Почетный гражданин Санкт-Петербурга“»'
		)
	def testOpenOpenCloseQuoteTranslation2(self):
		self.doTestQuoteTranslation(
			'Расходы на предоставление ежемесячных социальных выплат в соответствии с Законом Санкт-Петербурга «О звании «Почетный гражданин Санкт-Петербурга»',
			'Расходы на предоставление ежемесячных социальных выплат в соответствии с Законом Санкт-Петербурга «О звании „Почетный гражданин Санкт-Петербурга“»'
		)
	def testMixedQuoteTranslation(self):
		self.doTestQuoteTranslation(
			'Содержание Санкт-Петербургского государственного казенного учреждения «Дирекция по организации дорожного движения Санкт-Петербурга"',
			'Содержание Санкт-Петербургского государственного казенного учреждения «Дирекция по организации дорожного движения Санкт-Петербурга»'
		)
		# tricky quotes:
		# punctuation inside
		# 'Расходы на проведение мероприятий по реализации Комплексной программы "Наука. Промышленность. Инновации." в Санкт-Петербурге на 2012-2015 годы'
		# one opening, one closing, two opening, one closing
		# 'Бюджетные инвестиции на увеличение уставного капитала ОАО "Западный скоростной диаметр" в рамках реализации ДЦП СПб "Финансирование создания в Санкт-Петербурге автомобильной дороги "Западный скоростной диаметр"'

	def testUnusedManualTranslations(self):
		t=translators.CategoryNameTranslator([
			'foo','bar',
			'qwe','rty',
			'asd','fgh',
		])
		tr=t.translateWithReport('qwe')
		self.assertEqual(t.getUnusedManualTranslations(),{'foo','asd'})

if __name__=='__main__':
	unittest.main()
