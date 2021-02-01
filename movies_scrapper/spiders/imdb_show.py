import json
import pprint

import scrapy
from scrapy.http import HtmlResponse
from scrapy.utils.response import open_in_browser

from ..items import ImdbShow


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
                print(f'scraping {show["imdb"]}')
                if show['imdb']:
                    yield scrapy.Request(url='https://www.imdb.com/title/tt0' + show['imdb'], callback=self.parse)
            # show['imdb']
            yield  scrapy.Request(url='https://www.imdb.com/title/tt'+'02006371',callback=self.parse)
    def parse(self, response:HtmlResponse):
        item=ImdbShow()
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
