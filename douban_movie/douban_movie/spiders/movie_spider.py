# -*- coding: utf-8 -*-
from scrapy.spiders import CrawlSpider,Rule
from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from scrapy.linkextractors import LinkExtractor
from douban_movie.items import DoubanMovieItem, DoubanShortComment
import re
import logging
from pymongo import MongoClient
from scrapy.conf import settings

# pattern define
lang_pattern_str =  ".*语言:</span> (.+?)<br>".decode("utf8")
region_pattern_str = ".*制片国家/地区:</span>(.+?)<br>".decode("utf8")
dialect_pattern_str = ".*又名:</span>(.+?)<br>".decode("utf8")
episode_num_pattern_str = ".*集数:</span>(.+?)<br>".decode("utf8")
single_time_pattern_str = ".*单集片长:</span>(.+?)分钟".decode("utf8")

language_pattern = re.compile(lang_pattern_str,re.S)
region_pattern = re.compile(region_pattern_str,re.S)
dialect_pattern = re.compile(dialect_pattern_str,re.S)
episode_num_patter = re.compile(episode_num_pattern_str,re.S)
single_time_pattern = re.compile(single_time_pattern_str,re.S)
# end pattern define

class DoubanMovieSpider(CrawlSpider):
    name = "doubanmovie"
    allowed_domain = ["movie.douban.com"]
    handle_httpstatus_list = [404, 500, 400, 301, 302]
    
    movie_url_pattern  = u"https://movie.douban.com/subject/{0}/"
    comment_url_pattern = u'https://movie.douban.com/subject/{0}/comments?sort=new_score&status=P'
    
    def __init__(self,*a,**kw):
        super(DoubanMovieSpider,self).__init__(*a,**kw)
        client = MongoClient()
        db = client.movie
        self.id_list = db.id_list
        self.fail_list = db.fail_list
        self.movies = db.movies
        self.comments = db.comments

        self.max_id_in_list = 5
        self.max_retry_times = 5

        cookie_file = settings.get('COOKIE_FILE',None)  # 带着Cookie向网页发请求
        self.cookie = {}
        if cookie_file:
            for line in open(cookie_file):
                k,v = line.strip().split("\t")
                self.cookie[k] = v

        # 对请求的返回进行处理的配置
        self.meta = {
            'dont_redirect': True,  # 禁止网页重定向
            'handle_httpstatus_list': self.handle_httpstatus_list # 对哪些异常返回进行处理
        }

    def add_movie(self, item):
        if self.movies.find_one({"movie_id":item['movie_id']}):
            print(u"Movie {0} is already in database".format(item['movie_id']))
        else:
            self.movies.insert_one(dict(item))

    def get_next_unparsed_movie(self):
        item = self.id_list.find_one_and_update({"parsed":False},{"$set":{"parsed":True}})
        if item:
            return item['movie_id']
        
        for item in self.fail_list.find({"retry":{"$lt":self.max_retry_times}}):
            self.fail_list.update_one({"movie_id":item['movie_id']},{"$inc":{"retry":1}})
            return item['movie_id']

        return None

    def start_requests(self):
        initial_requests = []
        while len(initial_requests) < self.max_id_in_list:
            movie_id = self.get_next_unparsed_movie()
            if movie_id is not None:
                initial_requests.append(Request(self.movie_url_pattern.format(movie_id),callback=self.parse,cookies=self.cookie,meta=self.meta))
            else:
                break
        return initial_requests

    def add_array(self,name,arr,item):
        item[name]=[]
        for x in arr:
            item[name].append(x.strip())

    def parse_comments(self, response):

        rate_mapping = {u"很差":1,u"较差":2,u"还行":3,u"推荐":4,u"力荐":5}
        url = response.url
        movie_id = url.split('/')[-2].strip() 

        comments = response.xpath("//div[@class='comment']")
        for comment in comments:
            vote = comment.xpath(".//span[@class='votes']/text()").extract_first()
            user_name = comment.xpath(".//span[@class='comment-info']/a/text()").extract_first()
            rate = comment.xpath(".//span[@class='comment-info']//span[starts-with(@class,'all')]/@title").extract_first()
            rate = rate_mapping.get(rate,'0')
            short_comment = comment.xpath(".//p/text()").extract_first()

            item = DoubanShortComment()
            item['movie_id'] = movie_id
            item['vote'] = vote
            item['user_name'] = user_name
            item['comment'] = short_comment
            item['rate'] = rate

            self.comments.insert_one(dict(item))

        print(u"add {0} comments of movie id {1}".format(len(comments),movie_id))


    def parse(self, response):
        item = DoubanMovieItem()
        # get movie id
        url = response.url
        movie_id = url.split('/')[-2].strip()
        item["movie_id"] = movie_id
        try:
            if response.status in self.handle_httpstatus_list:
                print("Got status code {0}, continue to crawl other page".format(response.status))
                raise Exception("error status code {0}".format(response.status))
                
            is_episoder = False
            episodestr = response.xpath("//div[@class='episode_list']")
            if episodestr:
                is_episoder = True
            
            item['is_episode'] = is_episoder
            
            # get movie id
            #url = response.url
            #movie_id = url.split('/')[-2].strip() 
            #item["movie_id"] = movie_id
                
            # get movie name
            name = response.xpath('//div[@id="content"]/h1/span[1]/text()').extract_first()
            item["movie_name"] = name.strip() if name else u""

            if name is None or not name:
                raise Exception(u"Can not get title of movie id {0}".format(movie_id))
            
            print(u"start to mine movie %s with id %s"%(name,movie_id))
            
            #get movie year
            year = response.xpath('//div[@id="content"]/h1/span[2]/text()').extract_first()
            item["movie_year"] = year.strip(u"（）() ") if year else u""
            
            # get movie rate
            rate = response.xpath("//div[@class='rating_self clearfix']/strong/text()").extract_first()
            item["movie_rate"] = float(rate.strip() if rate else "-1")
            
            # get movie rate people
            rate_num = response.xpath("//span[@property='v:votes']/text()").extract_first()
            item["movie_rate_people"] = int(rate_num.strip() if rate_num else "-1")
            
            # initial release date
            release_date = response.xpath("//span[@property='v:initialReleaseDate']/@content").extract_first()
            item['movie_initial_release_date'] = release_date if release_date else "-1"
            
            #get seen and wish to see number
            seenwish = response.xpath("//div[@class='subject-others-interests-ft']//a//text()").extract()
            if seenwish:
                if len(seenwish) == 2:
                    item['movie_seen'] = int(seenwish[0][:-3])
                    item['movie_wishes'] = int(seenwish[1][:-3])
                if len(seenwish) == 3:
                    item['movie_seen'] = int(seenwish[1][:-3])
                    item['movie_wishes'] = int(seenwish[2][:-3])
            
            # get movie info
            info = response.xpath("//div[@id='info']")
            infoarray = info.extract()
            infostr = u''.join(infoarray).strip()
            
            #same region for movie and episode
            director = info.xpath("span[1]/span[2]/a/text()").extract()
            if director:
                self.add_array("movie_director",director,item)
            
            writor = info.xpath("span[2]/span[2]/a/text()").extract()
            if writor:
                self.add_array("movie_writor",writor,item)
            
            actors = info.xpath("span[@class='actor']/span[2]/a/text()").extract()
            if actors:
                self.add_array("movie_actors",actors,item)

            types = info.xpath("span[@property='v:genre']/text()").extract()
            if types:
                self.add_array("movie_type",types,item)
            
            try:
                lang = re.search(language_pattern,infostr)
                if lang:
                    language = lang.group(1).strip()
                    item["movie_language"] = language
            except:
                pass

            try:
                regionmatch = re.search(region_pattern,infostr)
                if regionmatch:
                    region = regionmatch.group(1).strip()
                    item["movie_region"] = region
            except:
                pass
            
            try:
                dialectmatch = re.search(dialect_pattern,infostr)
                if dialectmatch:
                    dialect = dialectmatch.group(1).strip()
                    item["movie_dialect"] = dialect
            except:
                pass
            
            desc = response.xpath("//span[@property='v:summary']").xpath("string(.)").extract_first()
            desc = desc.strip() if desc else u""
            desc_all = response.xpath("//span[@class='all hidden']").xpath("string(.)").extract_first()
            item["movie_desc"] = desc_all.strip() if desc_all else desc
            
            tags = response.xpath("//div[@class='tags-body']/a/text()").extract()
            if tags:
                self.add_array("movie_tags",tags,item)
            
            pic = response.xpath("//div[@id='mainpic']/a/img/@src").extract_first()
            if pic:
                item["movie_pic_url"] = pic
            #end same region
            
            if is_episoder:
                episodenummatch = re.search(episode_num_patter,infostr)
                if episodenummatch:
                    episodenum = episodenummatch.group(1).strip()
                    item["episode_num"] = int(episodenum)
                singletimematch = re.search(single_time_pattern,infostr)
                if singletimematch:
                    singletime = singletimematch.group(1).strip()
                    item["movie_time"] = float(singletime if singletime else "-1")
            else:
                item['episode_num'] = 1                
                time = info.xpath("span[@property='v:runtime']/@content").extract_first()
                item["movie_time"] = float(time.strip() if time else "-1")

            # parse short comment
            yield Request(self.comment_url_pattern.format(movie_id), callback=self.parse_comments, cookies=self.cookie, meta=self.meta)
            
            self.add_movie(item)
            movie_id = self.get_next_unparsed_movie()
            yield Request(self.movie_url_pattern.format(movie_id),callback=self.parse,cookies=self.cookie,meta=self.meta)
            
                        
        except Exception as e:
            logging.info(u"failed movie: %s, Parse error:%s"%(item['movie_id'],str(e)))

            fail_item = self.fail_list.find_one({"movie_id":item['movie_id']})
            if fail_item is not None:
                self.fail_list.update_one({"movie_id":item['movie_id']},{"$inc":{"retry":1}})
            else:
                self.fail_list.insert_one({"movie_id":item['movie_id'],"retry":1})

            movie_id = self.get_next_unparsed_movie()
            yield Request(self.movie_url_pattern.format(movie_id),callback=self.parse,cookies=self.cookie,meta=self.meta)
