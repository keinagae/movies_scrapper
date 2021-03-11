import json
import pprint
import re
import urllib
from fuzzywuzzy import fuzz
import scrapy
from pymongo import MongoClient
from scrapy.http import HtmlResponse
from movies_scrapper.helpars import find_relevant_year_show_json
from scrapy.utils.response import open_in_browser
stop_words=['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"]
punctuation = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
from ..items import ImdbShow, ImdbId


def remove_special(value:str):
    return " ".join(re.sub("[-,:?]","",value.lower()).split())
db = MongoClient()
imdb = db.imfb

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
    name = 'imdb_id'
    total_shows=0
    found_shows=0
    # allowed_domains = ['https://www.imdb.com/']
    # start_urls = ['http://https://www.imdb.com//']
    def start_requests(self):
        for show in list(imdb.imdb_export.find({})):
            self.total_shows+=1
            params = {'q': show['title'], "ref_": "nv_sr_sm", 's': 'tt'}
            # params = {'q': "stephen king's the langoliers", "ref_": "nv_sr_sm", 's': 'tt'}
            yield scrapy.Request("https://www.imdb.com/find?" +
                                     urllib.parse.urlencode(params),
                                     callback=self.parse_title,
                                     cb_kwargs={'show': show},
                                     dont_filter=True)
            # break

    def parse_title(self,response:HtmlResponse,show):
        show_title=show['title'].lower()
        for ele in show_title:
            if ele in punctuation:
                show_title = show_title.replace(ele, "")
        show_title = " ".join([word for word in show_title.strip().split(" ") if not word in stop_words])
        raw_shows = response.xpath(
            ".//div[@id='main']//div[@class='findSection']/h3[contains(text(),'Titles')]/parent::div/table/tr/td[@class='result_text']")
        shows = []
        for imdb_show in raw_shows:
            is_episode = imdb_show.xpath("./small")
            episode_title=""
            episode_link=""
            if is_episode and len(is_episode) > 1:
                episode_title=imdb_show.xpath("./a[1]/text()").get()
                episode_link=imdb_show.xpath("./a[1]/@href").get()
                title = imdb_show.xpath("./small[2]/a/text()").get()
                link = imdb_show.xpath("./small[2]/a/@href").get()
            # else:
            title = imdb_show.xpath("./a[1]/text()").get()
            title_actual=title
            link = imdb_show.xpath("./a[1]/@href").get()
            imdbId=link.split("/")[-2]
            aka = imdb_show.xpath("./i/text()").get()
            aka_actual=aka
            title=title.lower()

            if aka:
                aka = aka.replace('"', "")
                aka=aka.lower()
            for ele in title:
                if ele in punctuation:
                    title = title.replace(ele, "")
            if aka:
                for ele in aka:
                    if ele in punctuation:
                        aka = aka.replace(ele, "")
                aka = "  ".join([word for word in aka.strip().split(" ") if not word in stop_words])
            title=" ".join([word for word in title.strip().split(" ") if not word in stop_words])

            found_year = [text.strip() for text in imdb_show.xpath("./text()").extract() if
                          text.strip() and not text.strip() == 'aka']
            found_year = found_year[0] if found_year else ""
            year = get_year(found_year)
            shows.append({
                "episode_title":episode_title,
                "episode_link":episode_link,
                "title": title if title else "",
                "link": link if link else "",
                "year": year if year else "",
                "aka": aka if aka else "",
                'imdbId':imdbId,
                "title_actual":title_actual,
                "aka_actual":aka_actual,
            })
        shows=list(map(lambda imdb_show:{**imdb_show,'title_accuracy': fuzz.ratio(imdb_show['title'], show_title),'aka_accuracy':fuzz.ratio(imdb_show['aka'], show_title)},shows))
        accurate_shows=list(filter(lambda show : show['title_accuracy']==100 or show['aka_accuracy']==100,shows))
        if accurate_shows:
            for imdb_show in accurate_shows:
                yield scrapy.Request(url='https://www.imdb.com' + imdb_show['link'], callback=self.parse_show,cb_kwargs={"show": show,'imdb_show':imdb_show})
        else:
            relevent_shows = list(
                filter(lambda show: show['title_accuracy'] >80 or show['aka_accuracy'] > 80, shows))
            if relevent_shows:
                if len(relevent_shows)>10:
                    relevent_shows_85 = list(
                        filter(lambda show: show['title_accuracy'] > 85 or show['aka_accuracy'] > 85, shows))
                    if relevent_shows_85:
                        if len(relevent_shows_85) > 10:
                            relevent_shows_90 = list(
                                filter(lambda show: show['title_accuracy'] > 90 or show['aka_accuracy'] > 90, shows))
                            if relevent_shows_90:
                                for imdb_show in relevent_shows_90:
                                    yield scrapy.Request(url='https://www.imdb.com' + imdb_show['link'],
                                                         callback=self.parse_show,
                                                         cb_kwargs={"show": show, 'imdb_show': imdb_show})
                            else:
                                for imdb_show in relevent_shows_85:
                                    yield scrapy.Request(url='https://www.imdb.com' + imdb_show['link'],
                                                         callback=self.parse_show,
                                                         cb_kwargs={"show": show, 'imdb_show': imdb_show})
                        else:
                            for imdb_show in relevent_shows_85:
                                yield scrapy.Request(url='https://www.imdb.com' + imdb_show['link'],
                                                     callback=self.parse_show,
                                                     cb_kwargs={"show": show, 'imdb_show': imdb_show})
                    else:
                        for imdb_show in relevent_shows:
                            yield scrapy.Request(url='https://www.imdb.com' + imdb_show['link'], callback=self.parse_show,
                                                 cb_kwargs={"show": show, 'imdb_show': imdb_show})
                else:
                    for imdb_show in relevent_shows:
                        yield scrapy.Request(url='https://www.imdb.com' + imdb_show['link'], callback=self.parse_show,
                                             cb_kwargs={"show": show, 'imdb_show': imdb_show})

    def parse_show(self, response:HtmlResponse,show,imdb_show):
        item=ImdbId(show=show['_id'])
        item.imdbId=imdb_show['imdbId']
        item.title=show['title']
        item.link=imdb_show['link']
        generas=response.xpath('//*[@id="titleStoryLine"]/div/h4[text()="Genres:"]/parent::div/a/text()').extract()
        item.genre=generas
        item.year=imdb_show['year']
        item.title_accuracy=imdb_show['title_accuracy']
        item.aka_accuracy=imdb_show['aka_accuracy']
        # item.show=show
        return item
        # yield scrapy.Request(url=response.urljoin('companycredits?ref_=tt_dt_co'),callback=self.parse_companies,cb_kwargs={'item':item,'url':url})

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
