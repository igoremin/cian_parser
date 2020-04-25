import datetime
import os
from .models import ObjectInfoDetails, ResultFile
from openpyxl import Workbook
from openpyxl.styles import NamedStyle, Font, Border, Side, Alignment, colors
from openpyxl.utils.exceptions import IllegalCharacterError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_results_xlsx_file():
    print('WRITE')

    file_name = f'{datetime.datetime.today().strftime("%d-%m-%Y_%H-%M")}.xlsx'

    wb = Workbook()

    sheet = wb['Sheet']
    wb.remove(sheet)

    wb.create_sheet('Результаты')
    sheet = wb['Результаты']

    sheet.column_dimensions['A'].width = 30
    sheet.column_dimensions['B'].width = 50
    sheet.column_dimensions['C'].width = 10
    sheet.column_dimensions['D'].width = 10
    sheet.column_dimensions['E'].width = 30
    sheet.column_dimensions['F'].width = 50
    sheet.column_dimensions['G'].width = 100
    sheet.column_dimensions['H'].width = 50
    sheet.column_dimensions['I'].width = 100
    sheet.column_dimensions['J'].width = 60
    sheet.column_dimensions['K'].width = 30

    search_results = ObjectInfoDetails.objects.all()

    header = NamedStyle(name="header")
    header.font = Font(bold=True, color=colors.RED, size=15)
    header.border = Border(bottom=Side(border_style="thin"))
    header.alignment = Alignment(horizontal="center", vertical="center")
    sheet.append(['Название', 'ЖК', 'Цена', 'Цена за метр', 'Телефон', 'Адресс', 'Время до метро', 'Параметры',
                  'Описание', 'Ссылки на фото', 'URL'])

    header_row = sheet[1]
    for cell in header_row:
        cell.style = header

    r = 0
    for result in search_results:

        data = [result.title, result.jk_name, result.price, result.price_for_m, result.phones, result.address,
                result.time_to_the_subway, result.params, result.description, result.photos, result.url]

        try:
            sheet.append(data)
            r += 1

        except IllegalCharacterError:
            pass

    path = os.path.join(BASE_DIR, f'media/results_files/')
    if os.path.isdir(path) is False:
        os.makedirs(path, mode=0o777)

    wb.save(f'{path}/{file_name}')

    new_file = ResultFile()
    new_file.result_file = f'results_files/{file_name}'
    new_file.save()
