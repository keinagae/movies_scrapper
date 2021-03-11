import logging
import re

import scrapy
from pymongo import MongoClient
from scrapy.http import HtmlResponse

from ..items import FernseItem

db = MongoClient()
stations = db.stations_new
logging.basicConfig(filename='fernse.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)


class FernseSpider(scrapy.Spider):
    name = 'fernse'

    # allowed_domains = ['https://www.fernsehserien.de/']
    # start_urls = ['http://https://www.fernsehserien.de//']

    def start_requests(self):
        self.count = 0
        self.received = 0
        station_names = [station for station in
                         sorted(list(stations.list_collections()), key=lambda station: station['name']) if
                         station['name'] not in [
                             'logs',
                             'empties',
                             '2019_3SAT',
                             '2019_ALPHA',
                             "2019_ARD",
                             "2019_ARTE",
                             "2019_BFS",
                             '2019_EinsFestival',
                             '2019_HF',
                             '2019_KKA',
                             '2019_N3_Radio_Bremen',
                             '2019_PHOENIX',
                             '2019_SWR_BW',
                             '2019_Tele_5',
                             '2019_VOX',
                             '2019_ZDF',
                             '2020_3SAT',
                             '2020_ALPHA',
                             '2020_ARD',
                             '2020_ARTE',
                             '2020_BFS',
                             '2020_DMAX',
                             '2020_DW-tv',
                             '2020_EinsFestival',
                             '2020_HF',
                             '2020_K1',
                             '2020_K1DOKU',
                             '2020_KKA'
                         ]]
        print(station_names)
        for station in station_names:
            print(f"----station {station['name']} -------")
            for show in stations[station['name']].find({}):
                title = re.sub('[^A-Za-z0-9 ]+', '', show['title'])
                title = title.replace("  ", " ")
                title = title.replace(" ", "-")
                yield scrapy.Request(
                    url='https://www.fernsehserien.de/suche/' + title,
                    dont_filter=True,
                    cb_kwargs={'show': show, 'station': station['name']}
                )

    def parse(self, response: HtmlResponse, show, station):
        self.count += 1
        print(f"processing {self.count}")
        if response.url.find("/suche/") > -1:
            results = response.xpath(
                '//*[@id="fs-frame-2"]/main/div/article/ul/li[contains(@class,"suchergebnis")]')
            if results:
                found_shows = []
                for result in results:
                    url = result.xpath("./a/@href").get()
                    title = result.xpath(
                        ".//span[@class='suchergebnis-titel']/text()").get()
                    years = response.xpath(
                        ".//span[@class='suchergebnis-wannwo']/text()").get()
                    if years:
                        years = years.replace("\xa0", '')
                    found_shows.append({
                        "url": "https://www.fernsehserien.de" + url,
                        "title": title,
                        "years": years
                    })
                final_shows = list(
                    filter(lambda x: x['title'] == show['title'], found_shows))
                if len(final_shows) == 1:
                    if final_shows[0]['url'].find("/filme/") > -1:
                        print("sending to film")
                        yield scrapy.Request(final_shows[0]['url'], dont_filter=True, callback=self.parse_film,
                                             cb_kwargs={'show': show, "station": station})
                    else:
                        print("sending to series")
                        yield scrapy.Request(final_shows[0]['url'] + "/episodenguide", dont_filter=True,
                                             callback=self.parse_serie,
                                             cb_kwargs={'show': show, "station": station})

            else:
                print(f" no results {response.url}")
        elif response.url.find("/filme/") > -1:
            yield scrapy.Request(response.url, dont_filter=True, callback=self.parse_film,
                                 cb_kwargs={'show': show, "station": station})
        else:
            # nav=response.xpath("/html/body//nav[@class='series-menu']/ul/li")
            # print(nav)
            yield scrapy.Request(response.url + "/episodenguide", dont_filter=True, callback=self.parse_serie,
                                 cb_kwargs={'show': show, "station": station})

    def parse_film(self, response: HtmlResponse, show, station):
        print("found film")
        found_show = FernseItem()
        found_show.url = response.url
        found_show.station = station
        found_show.show_id = show['show_id']
        title = response.xpath(
            '//*[@id="fs-frame-2"]/main/article/header/h1/text()').get()
        found_show.title = title
        duration = response.xpath(
            "//*[@id='fs-frame-2']/main/article/section/div[@class='spielfilm-spezi']/text()").get()
        if duration:
            start = duration.find("(")
            end = duration.find(")")
            if start > -1:
                duration = duration[start + 1:end]
        found_show.duration = duration
        released_at = response.xpath(
            '//*[@id="fs-frame-2"]/main/article/section/div[@class="serie-infos-erstausstrahlung"]/text()').extract()
        found_show.released_at = released_at
        production_companies = response.xpath(
            '//*[@id="fs-frame-2"]/main/article/section/ul[contains(@class,"cast-crew")]/li[@itemprop="productionCompany"]//dt/text()').extract()
        found_show.production_companies = production_companies
        return found_show

    def parse_serie(self, response: HtmlResponse, show, station):
        print(f"searching serie  {response.url}")
        seasons = response.xpath(
            '//*[@id="fs-frame-2"]/main/article/div/div/section/table/tbody[@itemprop="containsSeason"]')
        episodes = response.xpath(
            '//*[@id="fs-frame-2"]/main//tbody[@itemprop="containsSeason"]/tr[@itemprop="episode"]')
        clean_episodes = []
        for episode in episodes:
            url = episode.xpath(".//a[@itemprop='url']/@href").get()
            name = episode.xpath(".//span[@itemprop='name']/text()").get()
            released_at = episode.xpath(
                ".//td[@title='Das Erste']/a/text()").get()
            clean_episodes.append(
                {
                    "url": url,
                    "title": name,
                    "released_at": released_at
                }
            )
        found_episodes = list(
            filter(lambda x: x['title'] == show['subtitle'], clean_episodes))
        if len(found_episodes) == 1:
            print(
                f"episode found https://www.fernsehserien.de{found_episodes[0]['url']}")
            yield scrapy.Request(url='https://www.fernsehserien.de' + found_episodes[0]['url'],
                                 dont_filter=True,
                                 callback=self.parse_episode,
                                 cb_kwargs={'show': show, 'episode': found_episodes[0], "station": station})

        else:
            print(f"episode not found {len(found_episodes)}")

    def parse_episode(self, response: HtmlResponse, show, episode, station):
        print(f"scraping episode {response.url}")
        found_show = FernseItem()
        episode_id = response.url.split("-")[-1]
        found_show.show_id = show['show_id']
        found_show.station = station
        title = response.xpath(
            "//header[@class='page-header']//h1[@class='serien-titel']/a/text()").get()
        episode_title = response.xpath(
            '//*[@id="episode-' + episode_id + '"]/span[@itemprop="name"]/text()').get()
        series_number = response.xpath(
            '//*[@id="fs-frame-2"]/main/article/div/div/section/ul/li/section/div[@itemprop="episodeNumber"]/text()').get()
        duration = ""
        if series_number:
            start = series_number.find("(")
            end = series_number.find(")")
            if start > -1:
                duration = series_number[start + 1:end]
                series_number = series_number[0:start]
        found_show.title = title
        found_show.episode_title = episode_title
        found_show.series_number = series_number
        found_show.duration = duration
        found_show.url = response.url
        found_show.released_at = [episode['released_at']]
        production_companies = response.xpath(
            '//*[@id="fs-frame-2"]/main/article//section/ul[contains(@class,"cast-crew")]/li[@itemprop="productionCompany"]//dt/text()').extract()
        found_show.production_companies = production_companies
        return found_show
