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

Actually, you only need to run the code, it will create the collections automaticly. But after running for a while, you can add index to these collections to speed up searching.

```
use movie
db.id_list.createIndex("movie_id")
db.id_list.createIndex("state")
db.tag_list.createIndex("tag")
```

## RUN

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