# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient

from movies_scrapper.items import FernseItem, ImdbId


class IMDBIdScrapperPipeline:
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.count = 0

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        print(spider)
        self.count = 0
        self.client = MongoClient()
        self.db = self.client["imfb"]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item: ImdbId, spider):
        self.db.imdb_export.update_one(
            {"_id": item.show},
            {
                "$push": {"results": {
                    "Title":item.title,
                    "imdbId":item.imdbId,
                    "link":item.link,
                    'genre':item.genre,
                    'year':item.year,
                    'title_accuracy':item.title_accuracy,
                    'aka_accuracy':item.aka_accuracy
                }},
            },
        )
        return item


class MoviesScrapperPipeline:

    collection_name = 'scrapy_items'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.count=0

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        print(spider)
        self.count=0
        self.client = MongoClient()
        self.db = self.client["stations_new"]
        self.logs=self.client.logs

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item:FernseItem, spider):
        print(item)
        data={
            "fernsehserien_url":item.url,
            "fernsehserien_title":item.title,
            "fernsehserien_episode_title":item.episode_title,
            "fernsehserien_serie_number":item.series_number,
            "fernsehserien_duration":item.duration,
            "fernsehserien_production_companies":item.production_companies,
            "fernsehserien_released_at":item.released_at
        }
        res=self.db[item.station].find_one_and_update(
            {"show_id": item.show_id},
            {
                "$set": data
            }
        )
        self.logs[item.station].update_one(
        {"show_id": item.show_id},
        {
            "$setOnInsert": {"checked": 0},
        },
        upsert=True,
        )
        self.logs[item.station].update_one(
            {"show_id": item.show_id},
            {
                "$inc": {"checked": 1},
            },
        )
        self.count+=1
        print(f"count of items is {self.count},  {True if res else False}")
        return item
