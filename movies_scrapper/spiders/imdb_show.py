import json
import pprint
import re
import urllib

import scrapy
from scrapy.http import HtmlResponse
from movies_scrapper.helpars import find_relevant_year_show_json
from scrapy.utils.response import open_in_browser

from ..items import ImdbShow
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

class ImdbShowSpider(scrapy.Spider):
    name = 'imdb_show'
    # allowed_domains = ['https://www.imdb.com/']
    # start_urls = ['http://https://www.imdb.com//']
    def start_requests(self):
        data=[]
        with open('./sample.json','r') as file:
            data=json.loads(file.read())
            show =data[0]
            # print(f'scraping {show["imdb"]}')
            for show in data:
                # print(f'scraping {show["imdb"]}')
                if show['imdb']:
                    pass
                    yield scrapy.Request(url='https://www.imdb.com/title/tt0' + show['imdb'], callback=self.parse,cb_kwargs={"show":show})
                else:
                    params = {'q': show['title'], "ref_": "nv_sr_sm", 's': 'tt'}
                    if show['serie']=='0':
                        params['q'] = show['episodetitle']
                        yield scrapy.Request("https://www.imdb.com/find?" +
                                             urllib.parse.urlencode(params),
                                             callback=self.parse_episode_title,
                                             cb_kwargs={'show': show},
                                             dont_filter=True)
                    else:
                        yield scrapy.Request("https://www.imdb.com/find?" +
                                             urllib.parse.urlencode(params),
                                             callback=self.parse_title, cb_kwargs={'show': show},
                                             dont_filter=True)
            # show['imdb']
            # yield  scrapy.Request(url='https://www.imdb.com/title/tt'+'02006371',callback=self.parse,cb_kwargs={"show":show})

    def parse_episode_title(self,response:HtmlResponse,show):
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
            subtitle = " ".join(
                show.xpath("./a[1]/text()").get().replace("-", "").replace(":", "").replace(",", "").split())
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
                lambda imdb_show: all(
                    [
                        remove_special(imdb_show['title'].lower()) == remove_special(show['title'].lower()),
                        any(
                            [
                                remove_special(imdb_show['subtitle'].lower()) == remove_special(show['subtitle'].lower()),
                                remove_special(imdb_show['aka'].lower()) == remove_special(show['aka'].lower()),
                            ]
                        )
                    ]
                ),
                shows
            )
        )
        year_similar = []
        episode_similar = {}
        if show['episode']!='0':
            episode =int(show['episode'])
            if relavent_shows:
                episode_similar = list(
                    filter(
                        lambda imdb_show: episode in set(imdb_show['episodes']),
                        relavent_shows
                    )
                )
        found_project = {}
        if episode_similar:
            found_project = episode_similar[0]
        else:
            year_similar = list(
                filter(lambda imdb_show: show['year'].lower() in imdb_show['year'], relavent_shows))
            if year_similar and len(year_similar) == 1:
                found_project = year_similar[0]
            else:
                if len(relavent_shows) == 1:
                    found_project = relavent_shows[0]
        if found_project:
            yield scrapy.Request(url='https://www.imdb.com' + found_project['link'], callback=self.parse,
                                 cb_kwargs={"show": show})

    def parse_title(self,response:HtmlResponse,show):
        raw_shows = response.xpath(
            ".//div[@id='main']//div[@class='findSection']/h3[contains(text(),'Titles')]/parent::div/table/tr/td[@class='result_text']")
        shows = []
        for imdb_show in raw_shows:
            is_episode = imdb_show.xpath("./small")
            if is_episode and len(is_episode) > 1:
                continue
            aka = imdb_show.xpath("./i/text()").get()
            if aka:
                aka = aka.replace('"', "")
            title = imdb_show.xpath("./a[1]/text()").get()
            link = imdb_show.xpath("./a[1]/@href").get()
            found_year = [text.strip() for text in imdb_show.xpath("./text()").extract() if
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
                lambda imdb_show: any(
                    [
                        remove_special(imdb_show['title']) == remove_special(show['title']),
                        remove_special(imdb_show['aka']) == remove_special(show['title']),
                    ]
                ),
                shows
            )
        )

        found_project, flag = find_relevant_year_show_json(shows=relavent_shows, project=show)
        if len(relavent_shows) == 1 and not found_project:
            found_project = relavent_shows[0]

        if found_project:
            yield scrapy.Request(url='https://www.imdb.com' + found_project['link'], callback=self.parse,
                                 cb_kwargs={"show": show})

    def parse(self, response:HtmlResponse,show):
        item=ImdbShow()
        item.imdbId=show['imdb']
        item.title=show['title']
        generas=response.xpath('//*[@id="titleStoryLine"]/div/h4[text()="Genres:"]/parent::div/a/text()').extract()
        item.generas=generas
        coutries=response.xpath('//*[@id="titleDetails"]/div/h4[text()="Country:"]/parent::div/a/text()').extract()
        item.coutries=coutries
        story=response.xpath('//*[@id="titleStoryLine"]/h2/following-sibling::div//p//*/text()').get()
        if story:
            story=story.strip()
        item.plot=story
        url=response.url
        yield scrapy.Request(url=response.urljoin('companycredits?ref_=tt_dt_co'),callback=self.parse_companies,cb_kwargs={'item':item,'url':url})

    def parse_companies(self,response:HtmlResponse,item:ImdbShow,url:str):
        productions=response.xpath('//*[@id="production"]/following-sibling::ul[1]/li/a/text()').extract()
        distributors = response.xpath('//*[@id="distributors"]/following-sibling::ul[1]/li/a/text()').extract()
        item.productions=productions
        item.distributors=distributors
        yield scrapy.Request(url=url+'fullcredits#cast',callback=self.parse_cost_detail,cb_kwargs={'item':item,'url':url})

    def parse_cost_detail(self,response:HtmlResponse,item:ImdbShow,url:str):
        director=response.xpath('//*[@id="fullcredits_content"]/table/tbody/tr/td/a/text()').get()
        if director:
            director=director.strip()
        item.director=director
        raw_cost_members=response.xpath('//*[@id="fullcredits_content"]/table[@class="cast_list"]//tr[@class="odd" or @class="even"]')
        cost=[]
        for member in raw_cost_members:
            name=member.xpath('./td[2]/a/text()').get()
            if name:
                name=name.strip()
            character_infos=member.xpath('.//td[@class="character"]/descendant::*/text()').extract()
            character=" ".join([character.strip() for character in character_infos])
            if name:
                cost.append({
                    "name":name,
                    "character":character
                })
        # print(cost)
        item.cost=cost
        yield scrapy.Request(url=url+'awards?ref_=tt_dt_co', callback=self.parse_awards,
                             cb_kwargs={'item': item})


    def parse_awards(self,response:HtmlResponse,item:ImdbShow):
        award_titles=response.xpath('//*[@id="main"]/div/div/h3')
        winner_in=[]
        for award in award_titles:
            award_type=award.xpath("./text()").get().strip()
            win_award=award.xpath("./following-sibling::table[1]//tr/td[@class='title_award_outcome']")
            if win_award:
                award_rows=int(win_award.xpath("@rowspan").get())
                win_awards=win_award.xpath("./following-sibling::td | ./parent::tr/following-sibling::tr/td")
                wins=[]
                if win_awards:
                    win_awards=win_awards[0:award_rows]
                    for award in win_awards:
                        award_name=award.xpath("./text()").get().strip()
                        award_given_to=award.xpath("./a/text()").extract()
                        notes=award.xpath("./div[@class='award_detail_notes']/text() | ./div[@class='award_detail_notes']/descendant::*/text()").extract()
                        notes=" ".join([note.strip() for note in notes])
                        wins.append(
                            {
                                "cat":award_name,
                                'given_to':award_given_to,
                                'notes':notes
                            }
                        )

                winner_in.append(
                    {
                        "name":award_type,
                        "awards":wins
                    }
                )
        item.awards=winner_in
        return item
