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
departmentNameRe=re.compile('(?P<departmentName>.*)\((?P<departmentCode>...)\)')

for r in range(r,maxRow):
	number,name,sectionCode,categoryCode,typeCode,amount=(ws.cell(row=r,column=c).value for c in range(6))
	row={'year':2014}
	if not number:
		break
	elif not sectionCode:
		m=departmentNameRe.match(name)
		row['departmentName']=departmentName=m.group('departmentName')
		row['departmentCode']=departmentCode=m.group('departmentCode')
	else:
		row['departmentName']=departmentName
		row['departmentCode']=departmentCode
		row['categoryName']=categoryName=name
		row['sectionCode']=sectionCode
	rows.append(row)
else:
	raise Exception('no total line found')

for row in rows:
	print(row)
