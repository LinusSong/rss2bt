#-*-coding:utf-8 -*-
import re
import os
import sys
import sqlite3
import math
import base64
import time
import urllib2
import smtplib
from email.mime.text import MIMEText

import yaml
import feedparser

# The following four functions are used to parse feed.
def CatchFeedinfo(title, rss, HttpProxy):
    try:
        feed = parseFeed(rss)
        if feed.entries == []:
            time.sleep(5)
            feed = parseFeedwithUA(rss)
        if feed.entries == []:
            time.sleep(5)
            feed = parseFeedviaProxy(HttpProxy, rss)
    except:
        itemtitle = feedtime = infohash = ''
        mailadded = "Wrong RSS or banned————" + title + ':' + rss + '\n'
        itemlist = [(itemtitle, feedtime, infohash, mailadded)]
    else:
        itemlist = []
        for i in range(len(feed.entries)):
            feedtime = time.strftime("%Y-%m-%d %H:%M:%S",time.strptime(feed.entries[i].published,"%a, %d %b %Y %H:%M:%S +0800"))
            itemtitle = feed.entries[i].title
            infohash = base64.b16encode(base64.b32decode(feed.entries[i].enclosures[0].href[20:52])).lower()
            mailadded = itemtitle.encode('utf-8') + '  ' + feedtime.encode('utf-8') + '\n'
            itemlist.append((itemtitle, feedtime, infohash, mailadded))
    return itemlist

def parseFeedviaProxy(HttpProxy, RssUrl):
    proxy = urllib2.ProxyHandler( {"http":HttpProxy} )
    feedparser.USER_AGENT = ('Mozilla/5.0 (X11; Linux x86_64)'
                             ' AppleWebKit/537.36(KHTML, like Gecko) '
                             'Chrome/42.0.2311.135 Safari/537.36')
    feed = feedparser.parse(RssUrl, handlers = [proxy])
    return feed

def parseFeedwithUA(RssUrl):
    feedparser.USER_AGENT = ('Mozilla/5.0 (X11; Linux x86_64)'
                             ' AppleWebKit/537.36(KHTML, like Gecko) '
                             'Chrome/42.0.2311.135 Safari/537.36')
    feed = feedparser.parse(RssUrl)
    return feed

def parseFeed(RssUrl):
    feed = feedparser.parse(RssUrl)
    return feed

def mkdir(dldir,item):
    if os.path.exists(os.path.join(dldir,item)) == False:
        os.makedirs(os.path.join(dldir,item))

#This is used to extract episode number from title
def Cal_episode(title):
    tmplist = []
    tmplist.append(re.findall("(?<=第)\d+(?=集|话|話|局)",title.encode('utf-8')))
    tmplist.append(re.findall("(?<=【)\d+(?=】)|(?<=\[)\d+(?=\])",title.encode('utf-8')))
    tmplist.append(re.findall("(?<= )\d+(?= )",title.encode('utf-8')))
    tmplist.append(re.findall("(?<=- )\d+",title.encode('utf-8')))
    tmplist.append(re.findall("\d+(?=[v|V]\d{1})",title.encode('utf-8')))
    tmplist.append(re.findall("\d+\.5",title.encode('utf-8')))
    episode = None
    for i in tmplist:
        if len(i) == 1:
            episode = i[0]
            break
    return episode

#Query the title and pubdate of the last episode.
def Query_Last(cell,series):
    series = (series,)
    try:
        cell.execute('SELECT title,max(PubDate) from Updated WHERE series = (?);',series)
        a = cell.fetchone()
        LastTitle = a[0]
        LastPubDate = a[1]
    except:
        LastTitle = None
        LastPubDate = None
    return LastTitle,LastPubDate

#Calculate how long time has gone
def Cal_timegone(timestr):
    timegone = time.time() - time.mktime(time.strptime(timestr, '%Y-%m-%d %H:%M:%S'))
    return timegone

#Generate the executation command.
def Task(item, title, PubDate, infohash, dldir):
    normal = ("lx download -bt magnet:?xt=urn:btih:" + infohash.encode('utf-8') +
              " --continue --output '" + os.path.join(dldir,item).encode('utf-8') + "/'")
    newitem = (title.encode('utf-8') + ' || ' +
               PubDate.encode('utf-8') + ' || ' + infohash.encode('utf-8'))
    error = "echo \"" + normal + " # " + newitem + "\" >> taskerror.sh"
    execute = normal + ' || ' + error + '\n'
    return execute

#Send mail.
def sendmail(username, password, content):
    sender = username
    mailto = username
    smtpAddr = 'smtp.' + username[username.find('@')+1:]
    msg =MIMEText(content)
    msg['Subject'] = '今日新番'
    msg['to'] = mailto
    msg['From'] = sender
    smtp = smtplib.SMTP(smtpAddr)
    smtp.login(username,password)
    smtp.sendmail(sender,mailto,msg.as_string())
    smtp.quit()

def main():
    workpath = sys.path[0]
    task = open('lixiantask.sh','w')
    task.write('#!/bin/sh'+'\n')
    config = yaml.load(open(os.path.join(workpath,'config.yml')).read())
    username = config['global']['username']
    password = config['global']['password']
    dldir = config['global']['dldir']
    HttpProxy = config['global']['HttpProxy']
    tasks = config['tasks']
    conn = sqlite3.connect(os.path.join(workpath,'bangumi.db'))
    cell = conn.cursor()
    try:
        cell.execute("SELECT * FROM Updated;")
    except:
        cell.execute('''CREATE TABLE Updated
                  (weekday TEXT,series TEXT,title TEXT,episode INTEGER,
                  PubDate TEXT,team TEXT,infohash TEXT);''')
    mailcontent = ''
    for item in tasks.keys():
        mkdir(dldir,item)
        weekday = item[:3]
        series = item[4:]
        team = tasks[item].keys()[0]
        LastTitle,LastPubDate = Query_Last(cell,series)
        if LastTitle == None:
            pass
        elif Cal_timegone(LastPubDate) <= 572400:
            continue
        print item.encode('utf-8') + ',' + team.encode('utf-8'),
        title, PubDate, infohash, mailadded = CatchFeedinfo(item, tasks[item].values()[0], HttpProxy)[0]
        episode = Cal_episode(title)
        if title == None:
            mailcontent += mailadded
            continue
        if Cal_timegone(PubDate) < 5400:
            continue
        if LastTitle <> title:
            mailcontent += mailadded
            entry = (weekday,series,title,episode,PubDate,team,infohash)
            cell.execute('INSERT INTO Updated VALUES (?,?,?,?,?,?,?)',entry)
            conn.commit()
            task.write(Task(item, title, PubDate, infohash, dldir))
            print "Ok"
        elif Cal_timegone(LastPubDate) >= 777600:
            mailcontent += ("No update for over 9 days————" +
                            item.encode('utf-8') + ':' + tasks[item].values()[0] + '\n')
    if mailcontent <> '':
        try:
            sendmail(username, password, mailcontent)
        except:
            print mailcontent
    conn.close()

if __name__ == "__main__":
    main()
