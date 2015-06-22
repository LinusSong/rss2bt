# RssToXunlei_lixian
The script is exactly written for [share.dmhy.org](http://share.dmhy.org) and [xunlei_lixian](https://github.com/iambus/xunlei-lixian).

##Feature:
- Decode Base32 to Hex, since Xunlei doesn't accept Base32 encoded SHA-1 hash.
- Work as a rss parser. Because [share.dmhy.org](http://share.dmhy.org) has a very strict limit on your visit frequency, [flexget](http://flexget.com)  easily leads you to 403. The script greatly reduces your visit frequency.
- Use sqlite to record your download.

##Usage:
- 3rd-party libraries`Yaml` and `feedparser` are needed.
```
sudo pip install yaml feedparser
```
- Your need to create a config file called `config.yml`, which syntax is very similar with [flexget](http://flexget.com). A example has been given. `username` and `password` are used to send notification emails. I recommand `qq.com` as the notification e-mail, since it is faster than gmail. `dldir` is the download directory. `HttpProxy` is the proxy used in parsing feed. All of the arguments can leave blank.
- Run `python update.py`, then a shell script named `lixiantask.sh` will be created. Run it to start download.
- `complete.py` is used to complete your database and downloads. All the missing logs in the database will be completed and the shell commands will be created for the missing files.
