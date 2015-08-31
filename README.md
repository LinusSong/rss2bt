# RssToXunlei_lixian
The script is exactly written for [share.dmhy.org](http://share.dmhy.org) and [xunlei_lixian](https://github.com/iambus/xunlei-lixian).

##Feature:
- Decode Base32 to Base16, since Xunlei doesn't accept Base32 encoded SHA-1 hash.
- Work as a rss parser. Because [share.dmhy.org](http://share.dmhy.org) has a very strict limit on your visit frequency, [flexget](http://flexget.com)  easily leads you to 403. The script greatly reduces your visit frequency.
- Use sqlite to record your download.

##Configuration:
- 3rd-party libraries`yaml` and `feedparser` are needed.
```
sudo pip install yaml feedparser
```
- `transmissionrpc` is optional. It is needed if you want to use `transmission` to download when [xunlei_lixian](https://github.com/iambus/xunlei-lixian) fails.
```
sudo pip install yaml transmissionrpc
```
- Your need to create two config files called `config_global.yml` and `config_tasks.yml`, which syntax is very similar with [flexget](http://flexget.com). Examples have been given.
- All of the parameters in `config_global.yml` are optional:
 - `email_username` and `email_password` are used to send notification emails. `toMail` is the email which you use to receive the notification.
 - `dldir` is the download directory.
 - `HttpProxy` is the http proxy used when failing to parse feed normally.
 - `transmissionrpc_server`, `transmissionrpc_user`, `transmissionrpc_password`, `transmissionrpc_download_path` are for `transmission`.
- You can create `config_tasks.yml` by [Animelist](https://github.com/LinusSong/Animelist)

##Usage:
```
python rss2lx.py <commands> <parameters>
```

####commands and parameters:
- update [-download|--update-team|-nowait|-noxunlei] [-waitdays days]
- markup [-net|-db] [-w item]

####Explanation:
- download: download directly
- update-team: subscribe the current team for another team who publishes the latest episode most quickly.
- nowait: in case Xunlei doesn't finish downloading, the episode will not be updated into database in 1.5 hour after an eipsode publishes. This parameter revoke this limit.
- noxunlei: don't use Xunlei, use transmission directly.
- waitdays: 6.625 days are waited before another parse in default, and this parameter is to change it.
- net: make up the database from RSS feed.
- db: find the items which is not downloaded and write commands for them to lixiantask.sh
- w: only the item will be checked.

####Examples:
```
python rss2lx.py update -download # update database and download directly
python rss2lx.py markup -net -db -w Charlotte # make up the database about Charlotte and write commands for items which is not downloaded to lixiantask.sh
```

All failure will be record in  `taskerror.sh`.

##One more thing
I will share my bangumi list every quarter!
