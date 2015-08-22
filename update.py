#-*-coding:utf-8 -*-
import re
import os
import sys
import sqlite3
import base64
import time
import commands
import urllib2
import smtplib
from email.mime.text import MIMEText

import yaml
import feedparser

class Downloader(object):
    def __init__(self):
        self.workpath = sys.path[0]
        if '-d' in sys.argv:
            self.IsDownload = True
        else:
            self.IsDownload = False
        config_global = yaml.load(open(os.path.join(self.workpath,'config_global.yml')).read())
        self.username = config_global['email_username']
        self.password = config_global['email_password']
        self.dldir = config_global['dldir']
        self.toMail = config_global['toMail']
        self.HttpProxy = config_global['HttpProxy']
        self.transmissionrpc_server = config_global['transmissionrpc_server']
        self.transmissionrpc_user = config_global['transmissionrpc_user']
        self.transmissionrpc_password = config_global['transmissionrpc_password']
        self.transmissionrpc_download_path = config_global['transmissionrpc_download_path']
        config_tasks = yaml.load(open(os.path.join(self.workpath,'config_tasks.yml')).read())
        self.tasks = config_tasks
        self.mail = {'Update':[],'No Update over 9 Days':[], 'Not Yet Updated':[],
                     'Bad RSS or Banned': [],'Premature For Download':[],'Failed':[],
                     'Please Check Manually':[],'Use Transmissionrpc to Download':[]}

    def init_db_and_task(self):
        conn = sqlite3.connect(os.path.join(self.workpath,'bangumi.db'))
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM Updated;")
        except:
            cur.execute('''CREATE TABLE Updated
                      (weekday TEXT,series TEXT,title TEXT,episode INTEGER,
                      PubDate TEXT,team TEXT,infohash TEXT);''')
            conn.commit()
        finally:
            conn.close()
        task = open(os.path.join(self.workpath,'lixiantask.sh'),'w')
        task.write('#!/bin/sh'+'\n')
        task.close()

    def Generate_mail(self):
        content = ''
        for i in self.mail:
            if self.mail[i] != []:
                content += yaml.safe_dump({i:self.mail[i]},default_flow_style=False,allow_unicode=True)
        return content

    def Send_mail(self,content):
        "Send mail"
        sender = self.username
        smtpHost = 'smtp.' + self.username[self.username.find('@')+1:]
        msg =MIMEText(content)
        msg['Subject'] = '今日新番'
        msg['to'] = self.toMail
        msg['From'] = sender
        smtp = smtplib.SMTP_SSL(smtpHost,'465')
        smtp.ehlo()
        smtp.login(self.username,self.password)
        smtp.sendmail(sender,self.toMail,msg.as_string())
        smtp.quit()

class Entry(Downloader):
    def __init__(self, item_key):
        Downloader.__init__(self)
        self.item_key = item_key
        self.team = self.tasks[item_key]['team']
        self.rss = self.tasks[item_key]['rss'][self.team]
        self.weekday = item_key[:3]
        self.series = item_key[4:]
        if os.path.exists(os.path.join(self.dldir,item_key)) == False:
            os.makedirs(os.path.join(self.dldir,item_key))

    def GetFeedinfo(self):
        "The function is used to parse feed and extract information"
        def parseFeed(url,set_user_agent=False,HttpProxy=None):
            if HttpProxy == None:
                handlers = None
            else:
                proxy = urllib2.ProxyHandler( {"http":self.HttpProxy} )
                handlers = [proxy]
            if set_user_agent == True:
                feedparser.USER_AGENT = ('Mozilla/5.0 (X11; Linux x86_64)'
                                         ' AppleWebKit/537.36(KHTML, like Gecko) '
                                         'Chrome/42.0.2311.135 Safari/537.36')
            feed = feedparser.parse(url,handlers=handlers)
            return feed
        try:
            feed = parseFeed(self.rss)
            if feed.entries == []:
                time.sleep(5)
                feed = parseFeed(self.rss,set_user_agent=True)
            if feed.entries == []:
                time.sleep(5)
                feed = parseFeed(self.rss,set_user_agent=True,HttpProxy=self.HttpProxy)
        except:
            itemlist = []
        else:
            if feed.entries == []:
                itemlist = []
            else:
                itemlist = []
                for i in feed.entries:
                    try:
                        itemlist.append({'title':i.title,
                                         'PubDate':time.strftime("%Y-%m-%d %H:%M:%S",time.strptime(i.published,"%a, %d %b %Y %H:%M:%S +0800")),
                                         'infohash':base64.b16encode(base64.b32decode(i.enclosures[0].href[20:52])).lower(),
                                         'episode':Cal_episode(i.title),
                                         'magnet_origin':i.enclosures[0].href})
                    except:
                        continue
        return itemlist

    def Query_Last(self):
        "Query the title and pubdate of the last episode"
        try:
            conn = sqlite3.connect(os.path.join(self.workpath,'bangumi.db'))
            cur = conn.cursor()
            cur.execute('SELECT title,max(PubDate),episode from Updated WHERE series = (?);',(self.series,))
            LastTitle, LastPubDate, LastEpisode = cur.fetchone()
        except:
            LastTitle = LastPubDate = LastEpisode = None
        return LastTitle,LastPubDate,LastEpisode

    def Get_entry(self):
        LastTitle,LastPubDate,LastEpisode = self.Query_Last()
        if LastTitle == None:
            pass
        elif Cal_timegone(LastPubDate) <= 6*86400+15*3600:
            raise Exception("Premature For Parse")
        itemlist = self.GetFeedinfo()
        if itemlist == []:
            raise Exception("Bad RSS or Banned")
        self.title = itemlist[0]['title']
        self.PubDate = itemlist[0]['PubDate']
        self.infohash = itemlist[0]['infohash']
        self.episode = itemlist[0]['episode']
        self.magnet_origin = itemlist[0]['magnet_origin']
        if Cal_timegone(self.PubDate) < 5400:
            raise Exception("Premature For Download")
        if LastTitle == self.title and Cal_timegone(LastPubDate) >= 9*86400:
            raise Exception("No Update over 9 Days")
        elif LastTitle == self.title:
            raise Exception("Not Yet Updated")
        return (self.weekday,self.series,self.title,self.episode,self.PubDate,self.team,self.infohash)

    def Update_team(self):
        LastEpisode = self.Query_Last()[2]
        dict_tmp = {}
        config_tasks = yaml.load(open(os.path.join(self.workpath,'config_tasks.yml')).read())
        for team in config_tasks[self.item_key]['rss']:
            self.rss = config_tasks[self.item_key]['rss'][team]
            iteminfo = self.GetFeedinfo()[0]
            episode = iteminfo['episode']
            PubDate = iteminfo['PubDate']
            if episode != None and episode > LastEpisode:
                dict_tmp.update({team:PubDate})
        if dict_tmp != {}:
            MinPubDate = min([i for i in dict_tmp.values()])
            for team,PubDate in dict_tmp.items():
                if PubDate == MinPubDate:
                    config_tasks[self.item_key]['team'] = team
                    break
            yaml.safe_dump(config_tasks,file("config_tasks.yml","w"),default_flow_style=False,allow_unicode=True)

    def Update_db(self,entry_for_db):
        conn = sqlite3.connect(os.path.join(self.workpath,'bangumi.db'))
        cur = conn.cursor()
        cur.execute('INSERT INTO Updated VALUES (?,?,?,?,?,?,?)',entry_for_db)
        conn.commit()
        conn.close()

    def download(self,command,comment):
        print "Try to download directly"
        (status, output) = commands.getstatusoutput(command)
        if status != 0:
            try:
                import transmissionrpc
                print "Fail to download directly and try transmissionrpc"
                tc = transmissionrpc.Client(self.transmissionrpc_server,port=9091,user=self.transmissionrpc_user,password=self.transmissionrpc_password)
                tr = tc.add_torrent(self.magnet_origin,download_dir=os.path.join(self.transmissionrpc_download_path,self.item_key).encode('utf-8'))
                raise Exception("Use Transmissionrpc to Download")
            except:
                with open(os.path.join(self.workpath,'taskerror.sh'),'a') as target:
                    target.write(command + ' # ' + comment + '\n')
                raise Exception("Failed")

    def Generate_command(self):
        "Generate the executation command"
        command = ("lx download -bt magnet:?xt=urn:btih:" + self.infohash.encode('utf-8') +
                  " --continue --output '" + os.path.join(self.dldir,self.item_key).encode('utf-8') + "/'")
        comment = self.title.encode('utf-8') + '  ' + self.PubDate.encode('utf-8')
        return command, comment

def Cal_timegone(timestr):
    "Calculate how long time has gone"
    timegone = time.time() - time.mktime(time.strptime(timestr, '%Y-%m-%d %H:%M:%S'))
    return timegone

def Cal_episode(title):
    "Extract episode number from title"
    expressions = [r"(?<=第)\d+(?=集|话|話|局)",
                   r"(?<=【)\d+(?=】)|(?<=\[)\d+(?=\])",
                   r"(?<= )\d+(?= )",
                   r"(?<=- )\d+",
                   r"\d+(?=[v|V]\d{1})",
                   r"\d+\.5",
                   r"\d+(?=END|end|End| END| end| End)"
    ]
    for i in expressions:
        numbers = re.findall(i,title.encode('utf-8'))
        if len(numbers) == 1:
            return int(numbers[0])

def main():
    d = Downloader()
    d.init_db_and_task()
    for item_key in d.tasks.keys():
        print item_key,
        entry = Entry(item_key)
        try:
            entry_for_db = entry.Get_entry()
            entry.Update_db(entry_for_db)
            (command, comment) = entry.Generate_command()
            if d.IsDownload == True and entry.episode != None:
                entry.download(command,comment)
                d.mail['Update'].append({item_key:entry.team + ", " + str(entry.episode)})
                print 'Update'
            elif d.IsDownload == False and entry.episode != None:
                d.mail['Update'].append({item_key:entry.team + ", " + str(entry.episode)})
                with open(os.path.join(d.workpath,'lixiantask.sh'),'a') as task:
                    task.write(command + ' # ' + comment + '\n')
                print 'Update'
            elif entry.episode == None:
                d.mail['Please Check Manually'].append({item_key:entry.team})
                with open(os.path.join(d.workpath,'taskerror.sh'),'a') as task:
                    task.write(command + ' # ' + comment + '\n')
                print 'Please Check Manually'
        except Exception,reason:
            if str(reason) == "Premature For Parse":
                print str(reason)
            elif str(reason) in d.mail:
                print str(reason)
                d.mail[str(reason)].append({item_key:entry.team})
                if str(reason) == "No Update over 9 Days" and '--update-team' in sys.argv:
                    entry.Update_team()
            else:
                print Exception,str(reason)
    content = d.Generate_mail()
    print content
    if content != '':
        try:
            d.Send_mail(content)
        except:
            pass

if __name__ == "__main__":
    main()
