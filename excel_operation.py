import openpyxl

def export_to_excel(filename:str, data:list):
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    for row, line in enumerate(data):
        for col, dt in enumerate(line):
            worksheet.cell(column=col+1, row=row+1, value=dt)
    workbook.save(filename)
