import re
import urllib

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


def remove_special(value:str):
    return " ".join(re.sub("[-,:?]","",value.lower()).split())


def get_year(found_year):
    year = re.findall(r"\([0-9]{4}\)", found_year)
    if year:
        year = [int(year[0].replace("(", "").replace(")", "").strip().lower())]
    else:
        year = re.findall(r"\([0-9]{4}– \)", found_year)
        if year:
            year = [int(year[0].replace("(", "").replace("– )", "").strip().lower())]
        else:
            year = re.findall(r"\([0-9]{4} TV Movie\)", found_year)
            if year:
                year = [int(year[0].replace("(", "").replace(" TV Movie)", "").strip().lower())]
            else:
                year = re.findall(r"\([0-9]{4}-[0-9]{4}\)", found_year)
                if year:
                    year = [int(x.strip().lower()) for x in year[0].replace("(", "").replace(")", "").split("-")]
                else:
                    year = [0]
    return year


class ImdbSpider(scrapy.Spider):
    name = 'Imdb'

    # allowed_domains = ['https://www.imdb.com/']
    # start_urls = ['https://www.imdb.com/search/title/']

    def start_requests(self):
        for station in [station for station in
                        sorted(list(stations.list_collections()), key=lambda station: station['name']) if
                        station['name'] not in ['logs', 'empties']]:
            # station['name']
            station_collection = stations[station['name']]
            print(f"--------------- working on {station['name']} -----------------")
            for index, show in enumerate(station_collection.find({})):
                params={'q': show['title'], "ref_": "nv_sr_sm", 's': 'tt'}
                if show['subtitle']:
                    params['q'] = show['subtitle']
                    yield scrapy.Request("https://www.imdb.com/find?" +
                                         urllib.parse.urlencode(params),
                                         callback=self.subtitle_parse, cb_kwargs={'station': station, 'project': show},
                                         dont_filter=True)
                else:
                    yield scrapy.Request("https://www.imdb.com/find?" +
                                         urllib.parse.urlencode(params),
                                         callback=self.title_parse, cb_kwargs={'station': station, 'project': show},
                                         dont_filter=True)

    def subtitle_parse(self,response,station, project):
        raw_shows = response.xpath(
            ".//div[@id='main']//div[@class='findSection']/h3[contains(text(),'Titles')]/parent::div/table/tr/td[@class='result_text']")
        shows = []
        for show in raw_shows:
            is_episode = show.xpath("./small")
            episode_no = []
            if is_episode and len(is_episode) > 1:
                episode_no = " ".join(is_episode[0].xpath("./text()").extract())
                episode_no = re.findall(r"Episode (?:[0-9]+[,]?[0-9]*)", episode_no)
                if episode_no:
                    episode_no = episode_no[0].replace("Episode", "").strip().split(",")
                    episode_no = list(map(lambda epi: int(epi), episode_no))
            aka = show.xpath("./i/text()").get()
            if aka:
                aka = aka.replace('"', "")
            title = show.xpath("./small/a/text()").get()
            subtitle = " ".join(show.xpath("./a[1]/text()").get().replace("-","").replace(":","").replace(",","").split())
            link = show.xpath("./a[1]/@href").get()
            found_year = [text.strip() for text in show.xpath("./text()").extract() if
                          text.strip() and not text.strip() == 'aka']
            found_year = found_year[0] if found_year else ""
            year = get_year(found_year)
            shows.append({
                "title": title if title else "",
                "subtitle": subtitle if subtitle else "",
                "link": link if link else "",
                "year": year if year else "",
                "aka": aka if aka else "",
                "episodes": episode_no
            })
        relavent_shows = list(
            filter(
                lambda show: all(
                    [
                        remove_special(show['title'].lower()) == remove_special(project['title'].lower()),
                        any(
                            [
                                remove_special(show['subtitle'].lower()) ==remove_special(project['subtitle'].lower()) ,
                                remove_special(show['aka'].lower()) == remove_special(show['aka'].lower()),
                            ]
                        )
                    ]
                ),
                shows
            )
        )
        year_similar = []
        episode_similar = {}
        if project['dmbFolge']:
            current_episodes = set(map(lambda epi: int(epi), project['dmbFolge'].split(",")))
            if relavent_shows:
                episode_similar = list(
                    filter(
                        lambda show: (current_episodes & set(show['episodes'])),
                        relavent_shows
                    )
                )
        found_project = {}
        if episode_similar:
            found_project = episode_similar[0]
        else:
            year_similar = list(
                filter(lambda show: project['produktion_jahr'].lower() in show['year'] or project['dmbProduktionsJahr'].lower() in show['year'], relavent_shows))
            if year_similar and len(year_similar) == 1:
                found_project = year_similar[0]
            else:
                if len(relavent_shows) == 1:
                    found_project = relavent_shows[0]
        if found_project:
            station_collection = stations[station['name']]
            station_collection.find_one_and_update(
                project,
                {
                    "$set": {
                        "imdb_link": 'https://www.imdb.com' + found_project['link'],
                        "imdb_id": found_project['link'].replace("/title/", "").replace("/", ""),
                        "imdb_flag":"episode"
                    }
                },
                upsert=True
            )
            logs_doc.update(
                {"station": station['name']},
                {"$inc": {'imdb_found': +1, }}
            )
            yield response.follow(found_project['link'] + 'companycredits', callback=self.parse_company_credits,
                                  cb_kwargs=dict(station=station, project=project), dont_filter=True)
        else:
            params = {'q': project['title'], "ref_": "nv_sr_sm", 's': 'tt'}
            yield scrapy.Request("https://www.imdb.com/find?" +
                                 urllib.parse.urlencode(params),
                                 callback=self.title_parse, cb_kwargs={'station': station, 'project': project},
                                 dont_filter=True)

    async def title_parse(self, response, station, project):
        raw_shows = response.xpath(
            ".//div[@id='main']//div[@class='findSection']/h3[contains(text(),'Titles')]/parent::div/table/tr/td[@class='result_text']")
        shows = []
        for show in raw_shows:
            is_episode = show.xpath("./small")
            if is_episode and len(is_episode) > 1:
                continue
            aka = show.xpath("./i/text()").get()
            if aka:
                aka = aka.replace('"', "")
            title = show.xpath("./a[1]/text()").get()
            link = show.xpath("./a[1]/@href").get()
            found_year = [text.strip() for text in show.xpath("./text()").extract() if
                          text.strip() and not text.strip() == 'aka']
            found_year = found_year[0] if found_year else ""
            year = get_year(found_year)
            shows.append({
                "title": title if title else "",
                "link": link if link else "",
                "year": year if year else "",
                "aka": aka if aka else ""
            })
        relavent_shows = list(
            filter(
                lambda show: any(
                    [
                        remove_special(show['title']) == remove_special(project['title']),
                        remove_special(show['aka']) == remove_special(project['title']),
                    ]
                ),
                shows
            )
        )

        found_project, flag = find_relevant_year(shows=relavent_shows, project=project)
        if len(relavent_shows) == 1 and not found_project:
            found_project = relavent_shows[0]
            flag="title"

        if found_project:
            station_collection = stations[station['name']]
            station_collection.find_one_and_update(
                project,
                {
                    "$set": {
                        "imdb_link": 'https://www.imdb.com' + found_project['link'],
                        "imdb_id": found_project['link'].replace("/title/", "").replace("/", ""),
                        "imdb_flag": flag
                    }
                },
                upsert=True
            )
            logs_doc.update(
                {"station": station['name']},
                {"$inc": {'imdb_found': +1, }}
            )
            yield response.follow(found_project['link'] + 'companycredits', callback=self.parse_company_credits,
                                  cb_kwargs=dict(station=station, project=project), dont_filter=True)
        else:
            print(f"not found")

    async def parse_company_credits(self, response, station, project):
        id = {
            '_id': ObjectId(project['_id'], )
        }
        productions = response.xpath(
            "//div[@id='company_credits_content']//h4[@id='production']/following-sibling::ul[1]/li/a/text()").extract()
        item = {}
        item['imdb_productions'] = productions
        distributors = response.xpath(
            "//div[@id='company_credits_content']//h4[@id='distributors']/following-sibling::ul[1]/li/a/text()").extract()
        item['imdb_distributors'] = distributors
        station_collection = stations[station['name']]
        station_collection.find_one_and_update(
            id,
            {
                "$set": item
            },
            upsert=True
        )
        print("found")
