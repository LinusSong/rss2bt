# RssToXunlei_lixian
A python script to transform magnet of the Base32 encoded SHA-1 hash to magnet with 160-bit infohash in RSS of [dmhy](http://share.dmhy.org) and create commands for [xunlei_lixian](https://github.com/iambus/xunlei-lixian).
It seems very silly. Yes, beacause it is designed to run on Dreambox, a outmoded distribution of openwrt. Even python-sqlite3 can not work normally, as well as feedparser module. It is very luck feedparser can return the title and link of items, but it will fail when you want to get pubDate from feedparser. 
If your route or other devices has good hardware, you'd better choose Flexget and I also write a script to transform magnet format if you want to download form [dmhy](http://share.dmhy.org)
