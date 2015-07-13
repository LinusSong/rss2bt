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

def mkdir(dldir,item):
    if os.path.exists(os.path.join(dldir,item)) == False:
        os.makedirs(os.path.join(dldir,item))

def CatchFeedinfo(title, rss, HttpProxy):
    "The function is used to parse feed and extract information"
    try:
        feed = parseFeed(rss)
        if feed.entries == []:
            time.sleep(5)
            feed = parseFeed(rss,set_user_agent=True)
        if feed.entries == []:
            time.sleep(5)
            feed = parseFeed(rss,set_user_agent=True,HttpProxy=HttpProxy)
    except:
        itemtitle = feedtime = infohash = ''
        mailadded = "Wrong RSS or you are banned: " + title + '\n'
        itemlist = [(itemtitle, feedtime, infohash, mailadded)]
    else:
        itemlist = []
        for i in feed.entries:
            feedtime = time.strftime("%Y-%m-%d %H:%M:%S",time.strptime(i.published,"%a, %d %b %Y %H:%M:%S +0800"))
            itemtitle = i.title
            infohash = base64.b16encode(base64.b32decode(i.enclosures[0].href[20:52])).lower()
            mailadded = itemtitle.encode('utf-8') + '  ' + feedtime.encode('utf-8') + '\n'
            itemlist.append((itemtitle, feedtime, infohash, mailadded))
    return itemlist

def parseFeed(url,set_user_agent=False,HttpProxy=None):
    "Parse feed"
    if HttpProxy == None:
        handlers = None
    else:
        proxy = urllib2.ProxyHandler( {"http":HttpProxy} )
        handlers = [proxy]
    if set_user_agent == True:
        feedparser.USER_AGENT = ('Mozilla/5.0 (X11; Linux x86_64)'
                                 ' AppleWebKit/537.36(KHTML, like Gecko) '
                                 'Chrome/42.0.2311.135 Safari/537.36')
    feed = feedparser.parse(url,handlers=handlers)
    return feed

def Cal_episode(title):
    "Extract episode number from title"
    expressions = [r"(?<=第)\d+(?=集|话|話|局)",
                   r"(?<=【)\d+(?=】)|(?<=\[)\d+(?=\])",
                   r"(?<= )\d+(?= )",
                   r"(?<=- )\d+",
                   r"\d+(?=[v|V]\d{1})",
                   r"\d+\.5",
                   r"\d+(?=END|end|End| END| end| End)",
                   r"\d{2}"
    ]
    for i in expressions:
        numbers = re.findall(i,title.encode('utf-8'))
        if len(numbers) == 1:
            return numbers[0]

def Query_Last(cell,series):
    "Query the title and pubdate of the last episode"
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

def Cal_timegone(timestr):
    "Calculate how long time has gone"
    timegone = time.time() - time.mktime(time.strptime(timestr, '%Y-%m-%d %H:%M:%S'))
    return timegone

def Task(item, title, PubDate, infohash, dldir, workpath):
    "Generate the executation command"
    normal = ("lx download -bt magnet:?xt=urn:btih:" + infohash.encode('utf-8') +
              " --continue --output '" + os.path.join(dldir,item).encode('utf-8') + "/'")
    newitem = (title.encode('utf-8') + ' || ' +
               PubDate.encode('utf-8') + ' || ' + infohash.encode('utf-8'))
    error = "echo \"" + normal + " # " + newitem + "\" >> "+ os.path.join(workpath,"taskerror.sh")
    execute = normal + ' || ' + error + '\n'
    return execute

def sendmail(username, password, content):
    "Send mail"
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
    task = open(os.path.join(workpath,'lixiantask.sh'),'w')
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
        print item.encode('utf-8') + ',' + team.encode('utf-8')
        itemlist = CatchFeedinfo(item, tasks[item].values()[0], HttpProxy)
        if itemlist != []:
            title, PubDate, infohash, mailadded = itemlist[0]
        else:
            mailcontent += item.encode('utf-8') + ',' + team.encode('utf-8') + ": This RSS is wrong!"
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
            task.write(Task(item, title, PubDate, infohash, dldir,workpath))
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
