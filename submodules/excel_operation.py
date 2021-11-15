import datetime
import openpyxl
import json

#
#record = [tmp_id, tmp_name, date, fever_status, cmp_avg, obj_avg, amb_avg]
#record = [tmp_id, tmp_name, date,               cmp_avg, obj_avg, amb_avg]

def export_to_excel(filename:str, data:list):
    with open('thermometer_cfg.json', 'rt') as f:    # read configurations from the configuration file
        config = json.load(f)

    if config['system']['school_flag'] == 'True':
        dt = datetime.datetime.now()
        date_str = '{}/{}/{}'.format(dt.year, dt.month, dt.day)
        workbook = openpyxl.load_workbook(filename)
        worksheet = workbook['1年生投入シート']
        for row, line in enumerate(data):
            student_id   = line[0]
            student_name = line[1]
            student_temp = line[4]
            worksheet.cell(column=2, row=row+2, value=date_str)
            worksheet.cell(column=3, row=row+2, value=student_id)
            if student_temp < 37.0:
                worksheet.cell(column=4, row=row+2, value='37℃ 以下')
                worksheet.cell(column=5, row=row+2, value='')
            else:
                worksheet.cell(column=4, row=row+2, value='37℃ 以上')
                worksheet.cell(column=5, row=row+2, value=student_temp)
        workbook.save(filename)
    else:

