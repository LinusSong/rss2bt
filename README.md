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

##Usage:
- run `update.py` and a shell script `lixiantask.sh` will be created. You can run it manually.
 - Two parameters are acceptable. Use `-d` to download directly, and use `--change-team` to replace the current team with the team who publishes the latest episode most quickly when the current team hasn't update over 9 days.
 - All failure will be record in  `taskerror.sh`.
 
##One more thing
I will share my bangumi list every quarter!
