# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field

class TagItem(scrapy.Item):
    tag = scrapy.Field()
    # 0 - not_start
    # 1 - processing
    # 2 - finished
    state = scrapy.Field()
    page = scrapy.Field()

class DoubanMovieIdItem(scrapy.Item):
    movie_id = Field()
    movie_url = Field()
    parsed = Field()
    movie_tag = Field()
    page = Field()

    title = Field()
    alias = Field()
    rate = Field()
    rate_people = Field()
    description = Field()


class DoubanMovieItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass
