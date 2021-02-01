import scrapy


class FernseSpider(scrapy.Spider):
    name = 'fernse'
    # allowed_domains = ['https://www.fernsehserien.de/']
    # start_urls = ['http://https://www.fernsehserien.de//']

    def parse(self, response):
        pass
