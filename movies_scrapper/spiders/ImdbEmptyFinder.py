import scrapy
import urllib
from bson.objectid import ObjectId
import re
from pymongo import MongoClient

db = MongoClient()
stations = db.stations_new
logs_doc = stations.logs
db['stations_new']['logs'].update_many(
    {},
    {
        "$set":{"crew_united_found":0}
    }
)
empties=db['stations_new']['empties']


class ImdbemptyfinderSpider(scrapy.Spider):
    name = 'ImdbEmptyFinder'
    # allowed_domains = ['https://www.imdb.com/']
    # start_urls = ['http://https://www.imdb.com//']

    def start_requests(self):
        for show in empties.find({}):
            params = {'title': show['title'], 'countries': 'de'}
            yield scrapy.Request("https://www.imdb.com/search/title/?" +
                                 urllib.parse.urlencode(params),
                                 callback=self.search_parse, cb_kwargs={ 'project': show},
                                 dont_filter=True)
    async def search_parse(self, response, project):
        main = response.xpath(".//div[@id='main']")
        raw_shows = main.xpath(
            ".//div[@class='article']//div[@class='lister list detail sub-list']//div[@class='lister-item-content']"
            "//h3[@class='lister-item-header']//a[1]")
        shows = []
        for raw_show in raw_shows:
            title= raw_show.xpath("./text()").get()
            link= raw_show.xpath("./@href").get()
            found_year = raw_show.xpath(
                ".//h3[@class='lister-item-header']/span[contains(@class,'lister-item-year')]/text()")
            year=""
            if found_year:
                found_year = found_year.get()
                year = re.findall(r"\([0-9]{4}\)", found_year)
                if year:
                    year = year[0].replace("(", "").replace(")", "")
                else:
                    year = re.findall(r"\([0-9]{4}– \)", found_year)
                    if year:
                        year = year[0].replace("(", "").replace("– )", "")
                    else:
                        year = re.findall(r"\([0-9]{4} TV Movie\)", found_year)
                        if year:
                            year = year[0].replace("(", "").replace(" TV Movie)", "")
                        else:
                            year = re.findall(r"\([0-9]{4}-[0-9]{4}\)", found_year)
                            if year:
                                year = year[0].replace("(", "").replace(")", "").split("-")[0]
                            else:
                                year = ""
            shows.append({'title':title, 'link': link,'year':year,"countries":[]})
        # station_collection = stations[station['name']]
        relavent_shows = list(filter(lambda show: show['title'].lower() == project['title'].lower(), shows))
        year_similar = list(
            filter(lambda show: show['year'].lower() == project['produktion_jahr'].lower(), relavent_shows))
        found_project = {}
        if year_similar:
            found_project = year_similar[0]
        else:
            if len(relavent_shows) == 1:
                found_project = relavent_shows[0]

        if found_project:
            yield response.follow(found_project['link'] , callback=self.parse_country,cb_kwargs=dict(project=project), dont_filter=True)
            # print(
            #     f"total shows {len(shows)} relavent {len(relavent_shows)} year found {len(year_similar)} with title {project['title']} found")
        # else:
        #     print(
        #         f"total shows {len(shows)} relavent {len(relavent_shows)} year found {len(year_similar)} with title {project['title']} not found")
    def parse_country(self,response,project):
        station=stations[project['station']]
        details=response.xpath(".//div[@id='titleDetails']")
        countries = details.xpath("./div/h4[contains(text(),'Country:')]/parent::div/a/text()").extract()
        if "DE" in countries or "Germany" in countries:
            project.pop("station")
            if not station.find({"show_id":project['show_id']}).count()>0:
                station.insert_one(project)
                print("inserted")
            else:
                print("already present")