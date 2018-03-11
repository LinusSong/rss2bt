# rss2bt
Use RSS to parse your favourite videos and download them automatically.

##Requirements:
- python3
```
sudo pip install requests PyYAML feedparser bs4 transmissionrpc
```

##Feature:
- This script can work as a rss parser and set the time interval. Because [share.dmhy.org](http://share.dmhy.org) has a very strict limit on your visit frequency, [flexget](http://flexget.com) may lead you to 403.
- Use sqlite to record your download.
- Avoid to download the same episode pubulished by different uploaders or with different versions.

##Configuration:
- Your need to create two config files called `config_global.yml` and `config_tasks.yml`, which syntax is very similar with [flexget](http://flexget.com). Examples have been given.
- You can choose a download method at `config_global.yml`. There are 3 options, aria2, transmission, or writing to a text directly.
- You can create `config_tasks.yml` by [Animelist](https://github.com/LinusSong/Animelist)

##Usage:
```
python3 main.py <commands> <parameters>
```
Please use `python3 main.py -h` to read the detailed uasage.
