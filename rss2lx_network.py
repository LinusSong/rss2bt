#-*-coding:utf-8 -*-
import urllib
import urllib2
import feedparser
import smtplib
from email.mime.text import MIMEText

def CatchFeedinfo(rss, HttpProxy):
    try:
        feed = parseFeed(rss)
        if feed.entries == []:
            feed = parseFeedwithUA(rss)
        if feed.entries == []:
            feed = parseFeedviaProxy(HttpProxy, rss)
        feedtime = feed.entries[0].published
        itemtitle = feed.entries[0].title
        infohash = convhash(feed.entries[0].enclosures[0].href[20:52])
        infolist = [itemtitle, feedtime, infohash]
    except:
        infolist = ['','','']
    return infolist

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
    
def convhash(Base32):
    Dict = {'A':'0','B':'1','C':'2','D':'3','E':'4','F':'5','G':'6','H':'7',
            'I':'8','J':'9','K':'A','L':'B','M':'C','N':'D','O':'E','P':'F',
            'Q':'G','R':'H','S':'I','T':'J','U':'K','V':'L','W':'M','X':'N',
            'Y':'O','Z':'P','2':'Q','3':'R','4':'S','5':'T','6':'U','7':'V'}
    convdBase32 = ''
    for i in list(Base32):
        convdBase32 += Dict[i]
    return str(hex(int(convdBase32,32)))[2:-1]
            
def mail(username, password, content):
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
