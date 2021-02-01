import json
import re
import scrapy
from pymongo import MongoClient

db = MongoClient()
stations = db.remaining
logs_doc = stations.logs
db['remaining']['logs'].update_many(
    {},
    {
        "$set": {"crew_united_found": 0}
    }
)
# logging.basicConfig(filename='log.log', level=logging.DEBUG,
#                     format='%(asctime)s %(levelname)s %(name)s %(message)s')
# logger=logging.getLogger(__name__)
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
empties = db['remaining']['empties']


class CrewunitetemptyfinderSpider(scrapy.Spider):
    name = 'CrewUnitetEmptyFinder'

    # allowed_domains = ['https://www.crew-united.com/en/']
    # start_urls = ['http://https://www.crew-united.com/en//']

    def start_requests(self):
        for show in empties.find({}):
            payload = [
                *default_payload,
                {
                    "id": "searchTerm",
                    "settings": [],
                    "value": show['title'],
                },
            ]
            yield scrapy.Request(
                'https://www.crew-united.com/en/SearchApi/search.asp',
                callback=self.parse,
                method='POST',
                body=json.dumps(payload),
                dont_filter=True,
                headers=headers,
                cb_kwargs={'project': show}
            )

    def parse(self, response, project):
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
                countries = show.xpath(
                    "./div/div//ul[@class='opt-pipe']/li[contains(text(),'Germany') or contains(text(),'DE')]/text()").extract()
                title = re.sub(r"\([0-9]{4}\)|\([0-9]{4}-[0-9]{4}\)", '', heading).strip()
                year = re.findall(r"\([0-9]{4}\)", heading)
                if year:
                    year = year[0].replace("(", "").replace(")", "")
                else:
                    year = ""
                duration = re.findall(r"\([0-9]{4}-[0-9]{4}\)", heading)
                if duration:
                    year = duration[0].replace("(", "").replace(")", "").split("-")[0]
                show_info['title'] = title
                show_info['crew_united_url'] = url
                show_info['year'] = year
                show_info['duration'] = duration
                show_info["countries"]=countries
                productions = show.xpath(
                    "./div//table[contains(@class,'opt-key-value')]//tr/th[text()='Production']/parent::tr/td/span/a/text()").extract()
                show_info['productions'] = productions
                shows.append(show_info)
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
                if found_project['countries']:
                    station = stations[project['station']]
                    project.pop("station")
                    if not station.find({"show_id": project['show_id']}).count() > 0:
                        station.insert_one(project)
                        print("inserted")
                    else:
                        print("already present")
        except Exception as e:
            pass
