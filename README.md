# Douban Moive Spider

A douban movie spider based on scrapy. This project contains two spiders:

- movie id spider: using tags to crawl movie ids from the web
- movie info spider: using movie ids to crawl movie details

> This code is not optimized for performance, it calls the database in each request. And to avoid to be banned by the douban, I have set the download delay to be 1s and used the AutoThrottle module. Since the number of movies in douban is about 200k, so the speed is OK, you just need to run and wait.

## Prerequisite

I tested on following environment:

- Ubuntu 16
- python 2.7
    - I suggest you to use virtualenv or conda
- scrapy 1.5.0
    - You can refer to [scrapy install](https://docs.scrapy.org/en/latest/intro/install.html) to install scrapy.
- mongodb 3.4.13
    - refer to [mongodb install](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/) to install mongodb

I met some problem when I used python 3.6 to install scrapy, so I changed to python 2.7 at last.

## Database

Create a database 'movie' with following collections:
- tag_list: list of tags
- id_list: list of movie ids
- movies: movie info collection
- comments: movie short comments collection
- fail_list: fail to get these movie info 

Actually, you only need to run the code, it will create the collections automaticly. But after running for a while, you can add index to these collections to speed up searching.

```
use movie
db.id_list.createIndex("movie_id")
db.id_list.createIndex("state")
db.tag_list.createIndex("tag")
```

## RUN

### Get your cookies
Since douban will ban you spider if you didn't set the cookies, you need get your cookies first.

The cookies used in my project is a txt file, you need change it to your own cookies file in the setting.py::COOKIE_FILE. Cookie file contains key-value per line, and split key and value by tab('\t'). You can refer to [this article](https://www.tuicool.com/articles/eAFVz2) to get your cookies.

> Warning: your account may be blocked by douban if you run my spiders. My account is blocked now, but still can run the spider by using the cookies.

### Get the movie ids
Run the 'doubanidlist' spider to crawl movie ids by using tags:
```
cd douban_movie
scrapy crawl doubanidlist
```

### Get the movie info
Run the doubanmovie spider to crawl the movie info by movie id:
```
scrapy crawl doubanmovie
```

## Statistics

I ran the doubanidlist spider firstly, and ran for about 2 days, got 1374 tags and 20k movie ids.

doubanmovie spider is much slow, since it will crawl the movie info page and also the short comments page. I ran for about 5 days, and got 14k movies and 1.6m comments.