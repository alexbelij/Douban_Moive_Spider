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

## Sample

### tag item

```
{
        "_id" : ObjectId("5a8150e754491246d94dc3d5"),
        "state" : 2,
        "tag" : "爱情",
        "page" : 2259
}
```

### movie id item

```
{
        "_id" : ObjectId("5a8158745449121b4969fe74"),
        "movie_tag" : "爱情",
        "description" : "1997-11-01(东京电影节) / 1997-12-19(美国) / 1998-04-03(中国大陆) / 莱昂纳多·迪卡普里奥 / 凯特·温丝莱特 / 比利·赞恩 / 凯西·贝茨 / 弗兰西丝·费舍 / 格劳瑞亚·斯图尔特 / 比尔·帕克斯顿 / 伯纳德·希尔 / 大卫·沃纳 / 维克多·加博 / 乔纳森·海德...",
        "title" : "泰坦尼克号",
        "rate_people" : "(719418人评价)",
        "alias" : "铁达尼号(港/台)",
        "rate" : 9.2,
        "movie_id" : "1292722",
        "movie_url" : "https://movie.douban.com/subject/1292722/",
        "parsed" : true,
        "page" : 1
}
```

### movie item
```
{
        "_id" : ObjectId("5a883ed054491259cc05d7cf"),
        "movie_name" : "泰坦尼克号 Titanic",
        "is_episode" : false,
        "movie_region" : "美国",
        "movie_director" : [
                "詹姆斯·卡梅隆"
        ],
        "movie_wishes" : 32122,
        "episode_num" : 1,
        "movie_year" : "1997",
        "movie_tags" : [
                "爱情",
                "经典",
                "美国",
                "灾难",
                "浪漫",
                "感动",
                "奥斯卡",
                "1997"
        ],
        "movie_actors" : [
                "莱昂纳多·迪卡普里奥",
                "凯特·温丝莱特",
                "比利·赞恩",
                "凯西·贝茨",
                "弗兰西丝·费舍",
                "格劳瑞亚·斯图尔特",
                "比尔·帕克斯顿",
                "伯纳德·希尔",
                "大卫·沃纳",
                "维克多·加博",
                "乔纳森·海德",
                "苏茜·爱米斯",
                "刘易斯·阿伯内西",
                "尼古拉斯·卡斯柯恩",
                "阿那托利·萨加洛维奇",
                "丹尼·努齐",
                "杰森·贝瑞",
                "伊万·斯图尔特",
                "艾恩·格拉法德",
                "乔纳森·菲利普斯",
                "马克·林赛·查普曼",
                "理查德·格拉翰",
                "保罗·布赖特威尔",
                "艾瑞克·布里登",
                "夏洛特·查顿",
                "博纳德·福克斯",
                "迈克尔·英塞恩",
                "法妮·布雷特",
                "马丁·贾维斯",
                "罗莎琳·艾尔斯",
                "罗切尔·罗斯",
                "乔纳森·伊万斯-琼斯",
                "西蒙·克雷恩",
                "爱德华德·弗莱彻",
                "斯科特·安德森",
                "马丁·伊斯特",
                "克雷格·凯利",
                "格雷戈里·库克",
                "利亚姆·图伊",
                "詹姆斯·兰开斯特",
                "艾尔莎·瑞雯",
                "卢·帕尔特",
                "泰瑞·佛瑞斯塔",
                "凯文·德·拉·诺伊"
        ],
        "movie_rate_people" : 721872,
        "movie_pic_url" : "https://img3.doubanio.com/view/photo/s_ratio_poster/public/p457760035.jpg",
        "movie_type" : [
                "剧情",
                "爱情",
                "灾难"
        ],
        "movie_desc" : "1912年4月10日，号称 “世界工业史上的奇迹”的豪华客轮泰坦尼克号开始了自己的处女航，从英国的南安普顿出发驶往美国纽约。富家少女罗丝（凯特•温丝莱特）与母亲及未婚夫卡尔坐上了头等舱；另一边，放荡不羁的少年画家杰克（莱昂纳多·迪卡普里奥）也在码头的一场赌博中赢得了下等舱的船票。\n                                    \n                                　　罗丝厌倦了上流社会虚伪的生活，不愿嫁给卡尔，打算投海自尽，被杰克救起。很快，美丽活泼的罗丝与英俊开朗的杰克相爱，杰克带罗丝参加下等舱的舞会、为她画像，二人的感情逐渐升温。\n                                    \n                                　　1912年4月14日，星期天晚上，一个风平浪静的夜晚。泰坦尼克号撞上了冰山，“永不沉没的”泰坦尼克号面临沉船的命运，罗丝和杰克刚萌芽的爱情也将经历生死的考验。",
        "movie_language" : "英语 / 意大利语 / 德语 / 俄语",
        "movie_id" : "1292722",
        "movie_dialect" : "铁达尼号(港/台)",
        "movie_initial_release_date" : "1998-04-03(中国大陆)",
        "movie_seen" : 948695,
        "movie_rate" : 9.2,
        "movie_time" : 194,
        "movie_writor" : [
                "詹姆斯·卡梅隆"
        ]
}
```

### comment item
```
{
        "_id" : ObjectId("5a883edc54491259cc05d7d4"),
        "comment" : " 那对对死无所畏惧的老夫妇，那个不为外界干扰的乐队，那个为生而做一次假父亲的男人，那个为爱人吹响口哨的女人。都是为了一种心灵上的执着。\n        ",
        "movie_id" : "1292722",
        "rate" : 5,
        "vote" : "3576",
        "user_name" : "个篱"
}
```

## Re-thinking

Actually, this spider is quite slow. The main reason is I tried to avoid to be banned by douban, so I set download delay to 1s, and from the log of spider, the average speed is about 40 pages/min. 

things can be done:

- It is easy to modify or add new spider to crawl other resources from douban, such as books. 
- Also you can modify the code to run this spider on several machines as long as you can connect to the same mongo database to speed up.
