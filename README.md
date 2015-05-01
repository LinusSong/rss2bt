# RssToXunlei_lixian
The script is exactly designed for [share.dmhy.org](http://share.dmhy.org) and [xunlei_lixian](https://github.com/iambus/xunlei-lixian)(as well as [xunlei yuancheng](http://yuancheng.xunlei.com/)).

##The main feature:
- Decode Base32 to Hex, since Xunlei doesn't accept Base32 encoded SHA-1 hash.
- Work as a rss parser. You know, share.dmhy.org has a very strict limit on your visit frequency, [flexget](http://flexget.com)  easily leads you to be banned. The script greatly reduces your visit frequency.
- Use a xlsx file as database, which is easier checked than SQL.

##Config:

Openpyxl and feedparser are needed.
```
sudo pip install openpyxl feedparser
```
Two files is needed:
- `rss2lx.config`
The file include four lines: path, username, password, proxy. 
Path is your download path. The default path is the current path. 
Username and password are optional. They are used to send notification via e-mail. Not all e-mails are accepted. 
Proxy is optional. It must be a http proxy.
Example:
```
/mnt/sda1/
10000@gmail.com
123456
127.0.0.1:8080
```
- `bangumi.xlsx`
You should put this file at your download path defined in `rss2lx.config`.
The example is given.
##Usage
```
python rss2lx.py
```
