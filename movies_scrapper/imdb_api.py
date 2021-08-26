from ruia import Request,Response,Spider
from pymongo import MongoClient
import re
db=MongoClient()
imdb_api=db['imdb_api_2']
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
class ImdbAPISpider(Spider):

    api_key="k_5tzga32n"

    start_urls = ['https://imdb-api.com/',]
    async def parse(self, response):
        imdb_api.collection_names()
        for collection_name in imdb_api.collection_names():
            collection = imdb_api[collection_name]
            print("hi")
            i = 0
            for item in collection.find(
                    {"Produktion konsolidiert": {'$in': [None, "[]", "", "[][][]", "[][]"]}, 'checked': False,'error':False}):
                try:
                    if item['subtitle']:
                        if item['subtitle'].find("/") != -1:
                            collection.update_one(
                                {
                                    'show_id': item['show_id']
                                },
                                {
                                    "$set": {
                                        "checked": True
                                    }
                                }
                            )
                        else:
                            request = await self.request(
                                f'https://imdb-api.com/en/API/SearchEpisode/k_5tzga32n/{item["subtitle"]}',
                                metadata={'item': item, 'collection': collection}).fetch()
                            await self.parse_subtitle(request, item, collection)
                    else:
                        if item['title'].find("/") != -1:
                            collection.update_one(
                                {
                                    'show_id': item['show_id']
                                },
                                {
                                    "$set": {
                                        "checked": True
                                    }
                                }
                            )
                        else:
                            request = await  self.request(
                                f'https://imdb-api.com/en/API/SearchTitle/k_5tzga32n/{item["title"]}',
                                metadata={'item': item, 'collection': collection}).fetch()
                            await self.parse_title(request, item, collection)
                except Exception as e:
                    raise e
                    print(f"exceptionv{e}")
    async def parse_subtitle(self,response:Response,item,collection):
        if response.status==-1:
            if item['title'].find("/") != -1:
                collection.update_one(
                    {
                        'show_id': item['show_id']
                    },
                    {
                        "$set": {
                            "checked": True,
                            "error":True
                        }
                    }
                )
            print(f"status is {response.status}")
            return
        json=await response.json()
        if json['results']:
            results=json['results']
            results=list(filter(lambda show:show['title']==response.metadata['item']['subtitle'],results))
            if results:
                search_results=[]
                for show in results:
                    show['show_name']=re.sub(r"\([0-9]{4}\)||\(TV Episode\) -||\(TV Series\)||Episode [0-9]* -|| Season [0-9]* \|", "", show['description'],).strip()
                    search_results.append(show)
                if search_results:
                    if len(search_results) == 1:
                        print(
                            f"found episode {response.metadata['collection']['name']}  {response.metadata['item']['show_id']}")
                        request = await self.request(
                            f"https://imdb-api.com/en/API/Title/k_5tzga32n/{results[0]['id']}").fetch()
                        await self.parser_show(request, response.metadata['item'], response.metadata['collection'])
                    else:
                        year = response.metadata['item']['produktion_jahr'] if response.metadata['item']['produktion_jahr'] else ""
                        search_results = list(filter(lambda show: show['description'].find(year) != -1, search_results))
                        if results:
                            print(
                                f"found episode {response.metadata['collection']['name']}  {response.metadata['item']['show_id']}")
                            request = await self.request(
                                f"https://imdb-api.com/en/API/Title/k_5tzga32n/{results[0]['id']}").fetch()
                            await self.parser_show(request, response.metadata['item'], response.metadata['collection'])
        if json['errorMessage']:
            print(f"error {json['errorMessage']}")
        else:
            if json['results']:
                response.metadata['collection'].update_one(
                    {
                        'show_id': response.metadata['item']['show_id']
                    },
                    {
                        "$set": {
                            "checked": True
                        }
                    }
                )
            else:
                if item['title'].find("/") != -1:
                    collection.update_one(
                        {
                            'show_id': item['show_id']
                        },
                        {
                            "$set": {
                                "checked": True
                            }
                        }
                    )
                else:
                    request=await self.request(f'https://imdb-api.com/en/API/SearchTitle/k_5tzga32n/{response.metadata["item"]["title"]}',metadata={'item':item,'collection':collection}).fetch()
                    await self.parse_title(request,item,collection)


    async def parse_title(self,response:Response,item,collection):
        if response.status==-1:
            if item['title'].find("/") != -1:
                collection.update_one(
                    {
                        'show_id': item['show_id']
                    },
                    {
                        "$set": {
                            "checked": True,
                            "error":True
                        }
                    }
                )
            return
        json=await response.json()
        if json['results']:
            results = json['results']
            results = list(filter(lambda show: show['title'] == response.metadata['item']['title'], results))
            if results:
                if len(results)==1:
                    print(f"found show {results}")
                    request = await self.request(f"https://imdb-api.com/en/API/Title/k_5tzga32n/{results[0]['id']}").fetch()
                    await self.parser_show(request, response.metadata['item'], response.metadata['collection'])
                else:
                    if response.metadata['item']['produktion_jahr']:
                        year=response.metadata['item']['produktion_jahr']
                        results=list(filter(lambda show:show['description'].find(year)!=-1,results))
                        if results:
                            print(f"found show {response.metadata['collection']['name']}  {response.metadata['item']['show_id']}")
                            request = await self.request(
                                f"https://imdb-api.com/en/API/Title/k_5tzga32n/{results[0]['id']}").fetch()
                            await self.parser_show(request, response.metadata['item'], response.metadata['collection'])

        if json['errorMessage']:
            print(f"error {json['errorMessage']}")
        else:
            response.metadata['collection'].update_one(
                {
                    'show_id': response.metadata['item']['show_id']
                },
                {
                    "$set": {
                        "checked": True
                    }
                }
            )

    async def parser_show(self,response:Response,item,collection):
        json=await response.json()
        print(f"found companies {collection['name']}  {item['show_id']}")
        collection.update_one(
            {
                'show_id': item['show_id']
            },
            {
                "$set":{
                    "Produktion konsolidiert":json['companies'],
                    "found":True
                }
            }
        )



if __name__ == '__main__':
    ImdbAPISpider.start()