import re
from openpyxl import load_workbook

wb=load_workbook('fincom/pr03-2014-16.xlsx')
ws=wb.get_active_sheet()
maxRow=ws.get_highest_row()

for r in range(maxRow):
	c=ws.cell(row=r,column=0)
	if c.value==1:
		break
else:
	raise Exception('table start not found')

rows=[{}] # reserve first row for total
departmentNameRe=re.compile(r'(?P<departmentName>.*?)\s*\((?P<departmentCode>...)\)')

for r in range(r,maxRow):
	number,name,sectionCode,categoryCode,typeCode,amount=(ws.cell(row=r,column=c).value for c in range(6))
	row={'year':2014}
	if not number:
		row['totalAmount']=amount
		rows[0]=row
		break
	elif not sectionCode:
		m=departmentNameRe.match(name)
		row['departmentName']=departmentName=m.group('departmentName')
		row['departmentCode']=departmentCode=m.group('departmentCode')
		row['departmentAmount']=amount
	elif not typeCode:
		row['departmentName']=departmentName
		row['departmentCode']=departmentCode
		row['sectionCode']=sectionCode=sectionCode[:2]+sectionCode[-2:]
		row['categoryName']=categoryName=name
		row['categoryCode']=categoryCode
		row['departmentCategoryAmount']=amount
	else:
		row['departmentName']=departmentName
		row['departmentCode']=departmentCode
		# if sectionCode!=sectionCode[:2]+sectionCode[-2:]:
			# raise Exception('unexpected change of sectionCode')
		row['sectionCode']=sectionCode
		row['categoryName']=categoryName
		row['categoryCode']=categoryCode
		row['typeCode']=typeCode
		row['departmentCategoryTypeAmount']=amount
	rows.append(row)
else:
	raise Exception('no total line found')

for row in rows:
	print(row)
