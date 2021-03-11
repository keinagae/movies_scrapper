import asyncio
import json
from pprint import pprint
import re

from lxml.etree import Element
from pymongo import MongoClient
from ruia import Request,Spider,Response

db = MongoClient()
stations = db.stations
class FernseSpider(Spider):
    start_urls = [f'https://www.fernsehserien.de/',]

    async def parse(self, response:Response):
        root:Element=response.html_etree(await response.text())
        divs=root.xpath('.//div')
        print(divs)
        station = stations[stations.list_collection_names()[0]]
        for show in list(station.find({})[0:10]):
            title = re.sub('[^A-Za-z0-9 ]+', '', show['title'])
            title = title.replace("  ", " ")
            title = title.replace(" ", "-")
            response = await Request(
                url='https://www.fernsehserien.de/suche/' + title,
            ).fetch()
            yield self.paser_search(response,show)


    async def paser_search(self,response:Response,show):
        print(response.url,show['title'])
        # result=await response.json()
        # if result:
        #     res=list(filter(lambda x:x['a'] not in ['sm','sg'],result ))
        #     if res:
        #         pprint([res, {'title':show['title'],'year':show['produktion_jahr'],'dmb_year':show['dmbProduktionsJahr']}])


    # async def process_item(self, item: HackerNewsItem):
    #     """Ruia build-in method"""
    #     async with aiofiles.open('./hacker_news.txt', 'a') as f:
    #         await f.write(str(item.title) + '\n')

async def request_example():
    url = 'https://www.fernsehserien.de/fastsearch'
    headers = {
        'Cookie': 'PHPSESSID=9ts0udburo7801t0q07kobvu9e',
        'x-csrf-token': '$2y$10$7EeYSlFbTPlKTHCeKxRdCO2Tc9tAUtAkcY3v9muw4EGsHYrvOBklS'
    }
    data={"suchwort": "Chuzpe - Klops braucht der Mensch!"}
    request = Request(url=url, method='POST', data=data,headers=headers)
    response = await request.fetch()
    print(await  response.json())


if __name__ == '__main__':
    FernseSpider.start()
    # asyncio.get_event_loop().run_until_complete(request_example())