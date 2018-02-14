# -*- coding: utf-8 -*-

from scrapy.spiders import CrawlSpider,Rule
from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from scrapy.linkextractors import LinkExtractor
from douban_movie.items import TagItem, DoubanMovieIdItem
import logging
import time
from pymongo import MongoClient
from random import randint
from scrapy.conf import settings

class DoubanIdListSpider(CrawlSpider):
    name = "doubanidlist"
    allowed_domain = ["movie.douban.com"]

    tag_url_pattern = u'https://movie.douban.com/tag/{0}?start={1}&type=O'

    def __init__(self, *a, **kwargs):
        super(DoubanIdListSpider,self).__init__(*a,**kwargs)
        tag_cline = MongoClient()
        tag_db = tag_cline.movie
        self.id_list = tag_db.id_list
        self.tag_list = tag_db.tag_list

        self.batch_size = 20
        self.max_tag_in_list = 5

        cookie_file = settings.get('COOKIE_FILE',None)  # 带着Cookie向网页发请求
        self.cookie = {}
        if cookie_file:
            for line in open(cookie_file):
                k,v = line.strip().split("\t")
                self.cookie[k] = v

        # 对请求的返回进行处理的配置
        self.meta = {
            'dont_redirect': True,  # 禁止网页重定向
            'handle_httpstatus_list': [301, 302]  # 对哪些异常返回进行处理
        }


    def add_tag(self, tag, state=0, page=0):
        tagItem = TagItem()
        tagItem['tag'] = tag
        tagItem['state'] = state
        tagItem['page'] = page
        self.tag_list.insert_one(dict(tagItem))

    def add_movie_id(self, id, url, tag, page, title, alias, rate, rate_people, desc, parsed=False):
        item = DoubanMovieIdItem()
        item['movie_id'] = id
        item['movie_url'] = url
        item['parsed'] = parsed
        item['page'] = int(page)
        item['movie_tag'] = tag
        item['title'] = title
        item['alias'] = alias
        item['rate'] = rate
        item['rate_people'] = rate_people
        item['description'] = desc

        self.id_list.insert_one(dict(item))

    def start_requests(self):
        # reset the status
        self.tag_list.update_many({"state":1},{"$set":{"state":0}})

        initial_tags = [u'爱情',u'剧情',u'喜剧',u'科幻']
        initial_requests = []
        for tag in initial_tags:
            tag_item = self.tag_list.find_one({"tag":tag})
            if tag_item is None:
                self.add_tag(tag)
                initial_requests.append(Request(self.tag_url_pattern.format(tag,0),callback=self.parse,cookies=self.cookie,meta=self.meta))
            elif tag_item['state'] < 1:
                initial_requests.append(Request(self.tag_url_pattern.format(tag, tag_item['page']*self.batch_size),callback=self.parse,cookies=self.cookie,meta=self.meta))
                self.tag_list.update_one({"tag":tag},{"$set":{"state":1}})
        
        # try to find in db
        if len(initial_requests) < self.max_tag_in_list:
            for tag_item in self.tag_list.find({'state':{"$eq":0}}):
                if tag_item['tag'] not in initial_tags:
                    initial_requests.append(Request(self.tag_url_pattern.format(tag_item['tag'], int(tag_item['page']*self.batch_size)),callback=self.parse,cookies=self.cookie,meta=self.meta))
                    initial_tags.append(tag_item['tag'])
                    self.tag_list.update_one({"tag":tag_item['tag']},{"$set":{"state":1}})
                if len(initial_requests) == self.max_tag_in_list:
                    break
        return initial_requests[:self.max_tag_in_list]

    def extract_movie_id_info(self, response, this_page_num, tag):
        movies = response.xpath('//div[@class="article"]//div[@class="pl2"]')
        add_count = 0
        for node in movies:
            url = node.xpath("./a/@href").extract_first()
            movie_id = url.split("/")[-2]

            if self.id_list.find_one({"movie_id": movie_id}):
                print(u"existing movie id = %s"%(url))
                continue

            name = node.xpath("./a/text()").extract_first()
            name = name.strip("\/\n ") if name else ""
            alias = node.xpath("./a/span/text()").extract_first()
            rate = node.xpath(".//span[@class='rating_nums']/text()").extract_first()
            rate = float(rate) if rate else -1.0
            rate_people = node.xpath(".//span[@class='pl']/text()").extract_first()
            desc = node.xpath(".//p[@class='pl']/text()").extract_first()

            add_count += 1
            self.add_movie_id(movie_id,url,tag,this_page_num,name,alias,rate,rate_people,desc,False)

        print(u"add %d ids in tag %s and page %d"%(add_count,tag,this_page_num))
        print(u"total movie id num: {0}, tag num: {1}".format(self.id_list.count(), self.tag_list.count()))

    def parse(self, response):
        this_page_num = response.xpath('//span[@class="thispage"]/text()').extract_first()
        no_content = response.xpath("//div[@class='article']//p[@class='pl2']/text()").extract_first()
        tag = response.xpath("//span[@class='tags-name']/text()").extract_first()
        if tag is None:
            return 
        
        if this_page_num is None and no_content and u"没有找到符合条件的电影" in no_content:
            print(u'finish process tag %s'%(tag))
            self.tag_list.find_one_and_update({'tag':tag},{'$set':{'state':2}})
            #find an random tag
            un_mined_tag = self.tag_list.find_one({'state':{"$eq":0}})
            if un_mined_tag:
                print(u"go to mine tag %s from page %d"%(un_mined_tag['tag'], un_mined_tag['page']))
                yield Request(self.tag_url_pattern.format(un_mined_tag['tag'],int(un_mined_tag['page']*self.batch_size)),callback=self.parse,cookies=self.cookie,meta=self.meta)
        else:
            this_page_num = int(this_page_num if this_page_num else "1")
            # To avoid add too many rare tags
            has_next_page = response.xpath("//span[@class='next']/a/text()").extract_first()
            # add relate_tag
            if this_page_num == 1:
                print(u'process tag %s'%(tag))
                self.tag_list.find_one_and_update({'tag':tag},{'$set':{'state':1}})
                relate_tag = response.xpath("//div[@id='tag_list']/span/a/text()").extract()
                if has_next_page is not None and relate_tag:
                    for t in relate_tag:
                        ret =  self.tag_list.find_one({'tag':t})
                        if ret is None:
                            print(u"add new tag %s"%(t))
                            self.add_tag(t)
                        else:
                            print(u"tag %s already in database"%(t))

            print(u"start to parse tag %s at page %d"%(tag, this_page_num))     
            self.extract_movie_id_info(response,this_page_num,tag)       
            self.tag_list.find_one_and_update({'tag':tag},{'$set':{'page':this_page_num}})
            #find next page
            nextpage = response.xpath('//span[@class="next"]/a/@href').extract_first()
            
            if nextpage:
                yield Request(nextpage,callback=self.parse)
            else:
                #try to find next page
                print(u"no next page in tag %s, try to find next page %d"%(tag,this_page_num+1))
                if tag:
                    yield Request(self.tag_url_pattern.format(tag, this_page_num*self.batch_size) , callback = self.parse, cookies=self.cookie,meta=self.meta)
