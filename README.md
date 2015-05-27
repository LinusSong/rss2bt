# RssToXunlei_lixian
The script is exactly written for [share.dmhy.org](http://share.dmhy.org) and [xunlei_lixian](https://github.com/iambus/xunlei-lixian).

##Feature:
- Decode Base32 to Hex, since Xunlei doesn't accept Base32 encoded SHA-1 hash.
- Work as a rss parser. share.dmhy.org has a very strict limit on your visit frequency. Therefore, [flexget](http://flexget.com)  easily leads you to be banned. The script greatly reduces your visit frequency.
- Use sqlite to document your download.

##Usage:
- Yaml and feedparser are needed.
```
sudo pip install yaml feedparser
```
- Your need to create a config file called `config.yml`, which syntax is very similar with [flexget](http://flexget.com). A example has been given.  username and password are used to send notification emails. dldir is the download directory. HttpProxy is the proxy used in parsing feed.
- Run `python rsstoxunlei_lixian.py`, then a shell script named `lixiantask.sh` will be created. Run it to start download.
