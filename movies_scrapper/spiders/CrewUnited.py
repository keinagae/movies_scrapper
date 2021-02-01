import json
import logging
import re

import scrapy
from bson.objectid import ObjectId
from pymongo import MongoClient

from movies_scrapper.helpars import find_relevant_year

db = MongoClient()
stations = db.remaining
logs_doc = stations.logs
db['remaining']['logs'].update_many(
    {},
    {
        "$set": {"crew_united_found": 0}
    }
)
logging.basicConfig(filename='log.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)
default_payload = [
    {
        "id": "channel",
        "settings": [],
        "value": "season",
    },
    {
        "id": "shootingStatus",
        "settings": "OR",
        "value": [],
    },
    {
        "id": "movieType",
        "settings": "OR",
        "value": [],
    },
    {
        "id": "productionCountry",
        "settings": "OR",
        "value": [],
    },
    {
        "id": "region",
        "settings": "OR",
        "value": [],
    },
    {
        "id": "numberOfResults",
        "settings": [],
        "value": "",
    },
    {
        "id": "pageSize",
        "settings": [],
        "value": "100",
    },
    {
        "id": "sortOrder",
        "settings": [],
        "value": "score",
    },
    {
        "id": "pagination",
        "settings": [],
        "value": 1,
    },
    {
        "id": "displayStyle",
        "settings": [],
        "value": "card",
    }
]
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
def remove_special(value:str):
    return " ".join(re.sub("[-,:?]","",value.lower()).split())

class CrewunitedSpider(scrapy.Spider):
    name = 'CrewUnited'

    # allowed_domains = ['https://www.crew-united.com/en/projects/']
    # start_urls = ['http://https://www.crew-united.com/en/projects//']

    def start_requests(self):
        for station in [station for station in
                        sorted(list(stations.list_collections()), key=lambda station: station['name']) if
                        station['name'] not in ['logs', 'empties']]:
            station_collection = stations[station['name']]
            print(f"--------------- working on {station['name']} -----------------")
            for index, show in enumerate(station_collection.find({})):
                payload = [
                    *default_payload,
                    {
                        "id": "searchTerm",
                        "settings": [],
                        "value": show['title'],
                    },
                ]
                # print(show['title'])
                # print(f"requesting {show['title']}")
                yield scrapy.Request(
                    'https://www.crew-united.com/de/SearchApi/search.asp',
                    callback=self.parse,
                    method='POST',
                    body=json.dumps(payload),
                    dont_filter=True,
                    headers=headers,
                    cb_kwargs={'station': station, 'project': show}
                )
            # break

    async def parse(self, response, station, project):
        try:
            html_string = response.xpath("//searchResultRenderedContent/text()")[0].get()
            html_response = scrapy.http.HtmlResponse(response.url, body=html_string, encoding="utf-8")
            raw_shows = html_response.xpath(
                ".//li/div[@class='cu-ui-card-card opt-style-project js-cu-filter-result-element']//div[1]/span/a/parent::span/parent::div/parent::div")
            shows = []
            for show in raw_shows:
                show_info = {}
                heading = show.xpath("./div/span/a")[0].xpath("./text()").get()
                url = show.xpath("./div/span/a")[0].xpath("./@href").get()
                title = re.sub(r"\([0-9]{4}\)|\([0-9]{4}-[0-9]{4}\)", '', heading).strip()
                year = re.findall(r"\([0-9]{4}\)", heading)
                if year:
                    try:
                        year = [int(year[0].replace("(", "").replace(")", "").strip().lower())]
                    except ValueError:
                        year = [0]
                        print("oooooooooooooooooooooooooooooooooooooooooooops")
                else:
                    year = [0]
                duration = re.findall(r"\([0-9]{4}-[0-9]{4}\)", heading)
                if duration:
                    try:
                        year = [int(x.strip().lower()) for x in
                                duration[0].replace("(", "").replace(")", "").split("-")]
                    except ValueError:
                        print("noooooooooooooooooooooooooooooooops")
                        year=[0]
                show_info['title'] = title
                show_info['crew_united_url'] = url
                show_info['year'] = year
                show_info['duration'] = duration
                productions = show.xpath(
                    "./div//table[contains(@class,'opt-key-value')]//tr/th[text()='Production']/parent::tr/td/span/a/text()").extract()
                show_info['productions'] = productions
                shows.append(show_info)
            relavent_shows = list(filter(lambda show: remove_special(show['title'])==remove_special( project['title']), shows))
            found_project, flag = find_relevant_year(shows=relavent_shows, project=project)
            if len(relavent_shows) == 1 and not found_project:
                found_project = relavent_shows[0]
                flag = "title"
            if found_project:
                # productions=found_project['productions']
                to_update = {
                    # 'crew_united_productions':productions,
                    'crew_united_url': found_project['crew_united_url'],
                    'cu_flag': flag
                }
                item = {
                    '_id': ObjectId(project['_id'], )
                }
                station_collection = stations[station['name']]
                station_collection.find_one_and_update(
                    item,
                    {
                        "$set": to_update
                    },
                    upsert=True
                )
                logs_doc.update(
                    {"station": station['name']},
                    {"$inc": {'crew_united_found': +1, }}
                )
                yield response.follow(show_info['crew_united_url'], callback=self.parse_broadcast,dont_filter=True,
                                      cb_kwargs={'station': station, 'project': project})
            else:
                print("Not Found")
        except Exception as e:
            logger.error(e)

    def parse_broadcast(self, response, station, project):
        broadcast = response.xpath(
            ".//div[@id='releases-tv']/table//tr/td[text()='First showing']/parent::tr/td[not(text()='First showing')]")
        country = ""
        bc_station = ""
        bc_time = ""
        productions = response.xpath(
            ".//div[@id='production']/table/tbody/tr/td[2][not(contains(text(),'Koproduzent'))]/parent::tr/td[1]/span/a/text()").extract()
        koproduzent_productions = response.xpath(
            ".//div[@id='production']/table/tbody/tr/td[2][contains(text(),'Koproduzent')]/parent::tr/td[1]/span/a/text()").extract()
        if broadcast:
            country = broadcast[0].xpath("./text()").get()
            bc_station = broadcast[1].xpath("./text()").get()
            bc_time = broadcast[2].xpath("./text()").get()
        to_update = {
            "crew_united_productions": productions,
            "crew_united_koproduzent_productions": koproduzent_productions,
            'cu_first_showing_country': country,
            'cu_first_showing_station': bc_station,
            "cu_first_showing_date_time": bc_time
        }
        item = {
            '_id': ObjectId(project['_id'], )
        }
        station_collection = stations[station['name']]
        station_collection.find_one_and_update(
            item,
            {
                "$set": to_update
            },
            upsert=True
        )
        print(f"found")
        # print(f"Crawled {project['title']} no broadcast")
