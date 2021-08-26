import re
import urllib
import json
from ruia import Request,Spider,Response,Item,TextField,ElementField

class ImdbItem(Item):
    productions=TextField(css_select='#production')

class AsyncIterator:
    def __init__(self, seq):
        self.iter = iter(seq)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.iter)
        except StopIteration:
            raise StopAsyncIteration

class IMDBIdSpider(Spider):
    start_urls = [f'https://www.imdb.com/', ]

    async def parse(self, response: Response):
        with open('ids.json',mode='r') as json_file:
            json_data=json.loads(json_file.read())['data']
        async for show_id in AsyncIterator(json_data[:10]):
            yield Request(
                url=f'https://www.imdb.com/title/{show_id}/companycredits?ref_=tt_dt_co',
                callback=self.parse_companies
            )

    async def parse_companies(self,response:Response):
        print("heeeee")
        item:ImdbItem = await ImdbItem.get_item(html=await response.text())
        print(item.productions)

if __name__ == '__main__':
    IMDBIdSpider.start()