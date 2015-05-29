#-*-coding:utf-8 -*-
import re
import os
import sqlite3
import math
import time
import yaml
import urllib2
import feedparser
import smtplib
from email.mime.text import MIMEText

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
        feedtime = time.strftime("%Y-%m-%d %H:%M:%S",time.strptime(feed.entries[0].published,"%a, %d %b %Y %H:%M:%S +0800"))
        itemtitle = feed.entries[0].title
        infohash = convhash(feed.entries[0].enclosures[0].href[20:52])
        mailadded = itemtitle.encode('utf8') + '  ' + feedtime.encode('utf8') + '\n'
    except:
        itemtitle = feedtime = infohash = ''
        mailadded = "Wrong RSS or banned————" + title + ':' + rss + '\n'
    return itemtitle, feedtime, infohash, mailadded

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

# The function is used to covent Base32 encoded infohash to hex infohash.
def convhash(Base32):
    Dict = {'A':'0','B':'1','C':'2','D':'3','E':'4','F':'5','G':'6','H':'7',
            'I':'8','J':'9','K':'A','L':'B','M':'C','N':'D','O':'E','P':'F',
            'Q':'G','R':'H','S':'I','T':'J','U':'K','V':'L','W':'M','X':'N',
            'Y':'O','Z':'P','2':'Q','3':'R','4':'S','5':'T','6':'U','7':'V'}
    convdBase32 = ''
    for i in list(Base32):
        convdBase32 += Dict[i]
    tmp = str(hex(int(convdBase32,32)))[2:-1]
    lentmp = len(tmp)
    if lentmp < 40:
        tmp = '0' * (40-lentmp) + tmp
    return tmp

def mkdir(dldir,item):
    if os.path.exists(dldir+item) == False:
        os.makedirs(dldir+item)

#This is used to extract episode number from title
def Cal_episode(title):
    a = re.findall("(?<=第)\d+(?=集|话|話|局)",title.encode('utf8'))
    b = re.findall("(?<=【)\d+(?=】)|(?<=\[)\d+(?=\])",title.encode('utf8'))
    c = re.findall("(?<= )\d+(?= )",title.encode('utf8'))
    d = re.findall("(?<=- )\d+",title.encode('utf8'))
    if len(a) == 1:
        episode = a[0]
    elif len(b) == 1:
        episode = b[0]
    elif len(c) == 1:
        episode = c[0]
    elif len(d) == 1:
        episode = d[0]
    else:
        episode = None
    return episode

#Query the title and pubdate of the last episode.
def Query_Last(series):
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
def Task(item, title, PubDate, infohash):
    normal = ("lx download -bt magnet:?xt=urn:btih:" + infohash + 
                " --continue --output '" + dldir + 
                item.encode('utf8') + "/'")
    newitem = (title.encode('utf8') + ' || ' + 
               PubDate.encode('utf8') + ' || ' + infohash)
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

task = open('lixiantask.sh','w')
task.write('#!/bin/sh'+'\n')
config = yaml.load(open('config.yml').read())
username = config['global']['username']
password = config['global']['password']
dldir = config['global']['dldir']
HttpProxy = config['global']['HttpProxy']
tasks = config['tasks']
conn = sqlite3.connect('bangumi.db')
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
    series = re.findall(".*(?=,)",item[4:])[0]
    team = re.findall("(?<=,)[^,]*$",item)[0]
    LastTitle,LastPubDate = Query_Last(series)
    if LastTitle == None:
        pass
    elif Cal_timegone(LastPubDate) <= 572400: 
        continue
    print LastTitle,LastPubDate
    title, PubDate, infohash, mailadded = CatchFeedinfo(item, tasks[item], HttpProxy)
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
        task.write(Task(item, title, PubDate, infohash))
        print "Ok"
    elif Cal_timegone(lastPubDate) >= 777600:
        mailcontent += ("No update for over 9 days————" + 
                        item.encode('utf8') + ':' + tasks[item] + '\n')
if mailcontent <> '':
    try:
        sendmail(username, password, mailcontent)
    except:
        print mailcontent
conn.close()
