import re
import urllib

from lxml.etree import Element
from pymongo import MongoClient
from ruia import Request,Spider,Response

db = MongoClient()
imdb = db.imfb

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
        async for show in AsyncIterator(list(imdb.imdb.find({}))):
            print(show)
            params = {'q': show['Title'], "ref_": "nv_sr_sm", 's': 'tt'}
            response = await Request(
                url='https://www.imdb.com/find?'
                +urllib.parse.urlencode(params)
            ).fetch()
            yield self.paser_search(response, show)

    async def paser_search(self,response:Response):

if __name__ == '__main__':
    IMDBIdSpider.start()