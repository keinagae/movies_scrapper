# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from dataclasses import dataclass,field
from typing import List,Dict
import scrapy


class MoviesScrapperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass
@dataclass
class ImdbShow():
    director:str=''
    plot:str=''
    cost:List[Dict] = field(default_factory=list)
    generas:List[str]=field(default_factory=list)
    coutries:List[str]=field(default_factory=list)
    productions:List[str]=field(default_factory=list)
    distributors:List[str]=field(default_factory=list)
    awards:List[dict]=field(default_factory=list)