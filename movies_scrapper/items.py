# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from dataclasses import dataclass,field
from typing import List,Dict
import scrapy
from bson import ObjectId


@dataclass
class FernseItem:
    station:str=""
    show_id:str=""
    url:str=""
    title:str=""
    episode_title:str="",
    series_number:str=""
    duration:str=""
    production_companies:List[str]=field(default_factory=list)
    released_at:List[str]=field(default_factory=list)
@dataclass
class ImdbShow:
    imdbId:str=""
    title:str=""
    director:str=''
    plot:str=''
    cost:List[Dict] = field(default_factory=list)
    generas:List[str]=field(default_factory=list)
    coutries:List[str]=field(default_factory=list)
    productions:List[str]=field(default_factory=list)
    distributors:List[str]=field(default_factory=list)
    awards:List[dict]=field(default_factory=list)


@dataclass
class ImdbId:
    show: ObjectId
    imdbId:str=""
    title:str=""
    link:str=""
    genre:List[dict]=field(default_factory=list)
    year:List[dict]=field(default_factory=list)
    title_accuracy:int=0
    aka_accuracy:int=0
