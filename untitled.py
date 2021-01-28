import xml.etree.ElementTree as ET
from lxml import etree
from pathlib import Path
from openpyxl import Workbook
path = Path("./Archivdaten_2019")
files=[file for file in path.iterdir() if not file.is_dir()]
xmlfile=files[0]
xmlabs=xmlfile.absolute()
parser = etree.XMLParser(recover=True)
tree = etree.parse("./Archivdaten_2019/2019_ARD.xml",parser=parser)
file="2019_ARD"
shows=tree.xpath(".//daten/einfuegen/sendung//stammdaten")

def get_flatten(node,data):
    for item in node:
        if len(item)==0:
            text= item.text.strip() if item.text  else ''
            if item.tag in data.keys():
                if isinstance(data[item.tag],list):
                    data[item.tag].append(text)
                else:
                    data[item.tag]=[data[item.tag]]
            else:
                data[item.tag] = text
        else:
            # print(item.tag,end="--")
            get_flatten(item,data)
wb=Workbook()
ws=wb.create_sheet(file)

list_data=[]
for show in shows:
    showDict={}
    data={}
    get_flatten(show,data)
    data.pop('erstellungsdatum')
    list_data.append(data)
    # print(data)
    # print(len(show))
# ws.append(data)
# wb.save("my")