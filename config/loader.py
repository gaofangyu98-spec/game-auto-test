"""
配表加载器：从 .sql 配表文件里读取策划配表(Excel)数据。

为什么要从 .sql 里读 Excel：
  游戏策划的数值配置先做在 Excel 里，导出工具把整个 Excel 文件
  以"0x 开头的十六进制"形式塞进一条 SQL INSERT 语句里。
  所以配表文件虽然叫 .sql，里面真正有用的是那串十六进制。
"""
import re
import openpyxl
from io import BytesIO


def load_config(sql_file_path):
    """
    加载配表，返回字典列表
    :param sql_file_path:
    :return:
    """
    # 读 .sql 文件
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 抠出 0X 开头的十六进制
    match = re.search(r"0x([0-9A-Fa-f]+)", content)

    # 十六进制转为二进制
    excel_bytes = bytes.fromhex(match.group(1))

    # openpyxl 解析
    wb = openpyxl.load_workbook(BytesIO(excel_bytes))
    ws = wb.active

    # 读表（第一行）
    header = []
    for cell in ws[1]:
        if cell.value is not None:
            header.append(cell.value)
        else:
            break

    # 读数据
    data_list = []
    for row in ws.iter_rows(min_row=4, max_row=ws.max_row, values_only=True):
        if row[0] is None:
            continue
        row_dict = {}
        for i, header in enumerate(header):
            row_dict[header] = row[i] if i < len(row) else None
        data_list.append(row_dict)

    return data_list















