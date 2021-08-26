import json

import scrapy
from scrapy.http import HtmlResponse

from movies_scrapper.items import ImdbCompanies


class ImdbProductionsSpider(scrapy.Spider):
    name = 'imdb_productions'
    # allowed_domains = ['https://www.imdb.com/']
    start_urls = ['https://www.imdb.com/']

    def start_requests(self):
        with open('ids.json', mode='r') as json_file:
            json_data=json.loads(json_file.read())['data']
            for show_id in json_data:
                yield scrapy.Request(f'https://www.imdb.com/title/{show_id}/companycredits?ref_=tt_dt_co',
                                     callback=self.parse_production,
                                     cb_kwargs={'id':show_id},
                                     dont_filter=True)
    def parse_production(self,response:HtmlResponse,id):
        item=ImdbCompanies(id=id)
        if response.xpath('//*[@id="production"]').extract():
            item.productions=response.xpath('//*[@id="production"]/following-sibling::ul[1]/li/a/text()').extract()
        if response.xpath('//*[@id="distributors"]'):
            item.distributors=response.xpath('//*[@id="distributors"]/following-sibling::ul[1]/li/a/text()').extract()
        return item
