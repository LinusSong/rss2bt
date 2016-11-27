#-*-coding:utf-8 -*-
import re
import os
import sys
import sqlite3
import base64
import time
import subprocess
import urllib.request, urllib.error, urllib.parse
import smtplib
from email.mime.text import MIMEText

import yaml
import feedparser

blacklist = []
whitelist = []
mail = {'Update':[],'No Update over 9 Days':[], 'Not Yet Updated':[],
        'Bad RSS or Banned': [],'Premature For Download':[],'Failed':[],
        'Please Check Manually':[],'Use Transmissionrpc to Download':[]}

def print_help():
    print(
"""usage:
  update
    -d --download
    -u --update-team
    -nw --nowait
    -nx --noxunlei
    -wd --waitdays days
  makeup
    -net
    -db
    -wl item
  test
    """)

class Downloader(object):
    def __init__(self):
        self.workpath = sys.path[0]
        if '--download' in sys.argv or '-d' in sys.argv:
            self.IsDownload = True
        else:
            self.IsDownload = False
        if '--nowait' in sys.argv or '-nw' in sys.argv:
            self.IsWait = False
        else:
            self.IsWait = True
        if '--noxunlei' in sys.argv or '-nx' in sys.argv:
            self.IsXunlei = False
        else:
            self.IsXunlei = True
        if '--update-team' in sys.argv or '-u' in sys.argv:
            self.IsChangeteam = True
        else:
            self.IsChangeteam = False
        if '--waitdays' in sys.argv:
            self.waitdays = float(sys.argv[sys.argv.index('--waitdays')+1])
        elif '-wd' in sys.argv:
            self.waitdays = float(sys.argv[sys.argv.index('-wd')+1])
        else:
            self.waitdays = 6.625
        config_global = yaml.load(open(os.path.join(self.workpath,'config_global.yml'), encoding = 'utf-8').read())
        self.username = config_global['email_username']
        self.password = config_global['email_password']
        self.dldir = config_global['dldir']
        self.toMail = config_global['toMail']
        self.HttpProxy = config_global['HttpProxy']
        self.transmissionrpc_server = config_global['transmissionrpc_server']
        self.transmissionrpc_user = config_global['transmissionrpc_user']
        self.transmissionrpc_password = config_global['transmissionrpc_password']
        self.transmissionrpc_download_path = config_global['transmissionrpc_download_path']
        config_tasks = yaml.load(open(os.path.join(self.workpath,'config_tasks.yml'), encoding = 'utf-8').read())
        self.tasks = config_tasks
        if os.path.exists(self.dldir) == False:
            self.dldir = os.path.join(os.path.expanduser('~'),'Downloads','bangumi')

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

        with open(os.path.join(self.workpath,'lixiantask.sh'),'w', encoding = 'utf-8') as task:
            task.write('#!/bin/sh'+'\n')
        if not os.path.exists(os.path.join(self.workpath,'taskerror.sh')) or \
        open(os.path.join(self.workpath,'taskerror.sh'), encoding = 'utf-8').readlines()[0] != '#!/bin/sh\n':
            with open(os.path.join(self.workpath,'taskerror.sh'),'w', encoding = 'utf-8') as task:
                task.write('#!/bin/sh'+'\n')

    def Generate_mail(self):
        content = ''
        for i in mail:
            if mail[i] != []:
                content += yaml.safe_dump({i:mail[i]},default_flow_style=False,allow_unicode=True)
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

    def GetFeedinfo(self, **argv):
        "The function is used to parse feed and extract information"
        rss = argv.get("rss",self.rss)
        def parseFeed(url,set_user_agent=False,HttpProxy=None):
            if HttpProxy == None:
                handlers = None
            else:
                proxy = urllib.request.ProxyHandler( {"https":self.HttpProxy} )
                handlers = [proxy]
            if set_user_agent == True:
                feedparser.USER_AGENT = ('Mozilla/5.0 (X11; Linux x86_64)'
                                         ' AppleWebKit/537.36(KHTML, like Gecko) '
                                         'Chrome/42.0.2311.135 Safari/537.36')
            feed = feedparser.parse(url,handlers=handlers)
            return feed
        try:
            feed = parseFeed(rss,set_user_agent=True,HttpProxy=self.HttpProxy)
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
                                         'infohash':base64.b16encode(base64.b32decode(i.enclosures[0].href[20:52])).decode().lower(),
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
        elif Cal_timegone(LastPubDate) <= self.waitdays*86400:
            raise Exception("Premature For Parse")
        itemlist = self.GetFeedinfo()
        if itemlist == []:
            raise Exception("Bad RSS or Banned")
        self.title = itemlist[0]['title']
        self.PubDate = itemlist[0]['PubDate']
        self.infohash = itemlist[0]['infohash']
        self.episode = itemlist[0]['episode']
        self.magnet_origin = itemlist[0]['magnet_origin']
        if self.IsWait == True and Cal_timegone(self.PubDate) < 5400:
            raise Exception("Premature For Download")
        if LastTitle == self.title and Cal_timegone(LastPubDate) >= 9*86400:
            raise Exception("No Update over 9 Days")
        elif LastTitle == self.title:
            raise Exception("Not Yet Updated")
        return (self.weekday,self.series,self.title,self.episode,self.PubDate,self.team,self.infohash)

    def Update_team(self):
        LastEpisode = self.Query_Last()[2]
        dict_tmp = {}
        config_tasks = yaml.load(open(os.path.join(self.workpath,'config_tasks.yml'), encoding = 'utf-8').read())
        for team in config_tasks[self.item_key]['rss']:
            rss = config_tasks[self.item_key]['rss'][team]
            iteminfo = self.GetFeedinfo(rss=rss)[0]
            episode = iteminfo['episode']
            PubDate = iteminfo['PubDate']
            if episode != None and episode > LastEpisode:
                dict_tmp.update({team:PubDate})
        if dict_tmp != {}:
            MinPubDate = min([i for i in list(dict_tmp.values())])
            for team,PubDate in list(dict_tmp.items()):
                if PubDate == MinPubDate:
                    config_tasks[self.item_key]['team'] = team
                    self.team = team
                    self.rss = config_tasks[self.item_key]['rss'][self.team]
                    yaml.safe_dump(config_tasks,file("config_tasks.yml","w"),default_flow_style=False,allow_unicode=True)
                    return self.team, self.rss

    def Update_db(self,entry_for_db):
        conn = sqlite3.connect(os.path.join(self.workpath,'bangumi.db'))
        cur = conn.cursor()
        cur.execute('INSERT INTO Updated VALUES (?,?,?,?,?,?,?)',entry_for_db)
        conn.commit()
        conn.close()

    def download(self,command,comment):
        if os.path.exists(os.path.join(self.dldir,self.item_key)) == False:
            os.makedirs(os.path.join(self.dldir,self.item_key))
        if self.IsXunlei == True:
            print("Try to download directly")
            (status, output) = subprocess.getstatusoutput(command)
        if self.IsXunlei == False or status != 0:
            try:
                import transmissionrpc
                print("try transmissionrpc")
                tc = transmissionrpc.Client(self.transmissionrpc_server,port=9091,user=self.transmissionrpc_user,password=self.transmissionrpc_password)
                tr = tc.add_torrent(self.magnet_origin,download_dir=self.transmissionrpc_download_path + '/' + self.item_key)
            except:
                with open(os.path.join(self.workpath,'taskerror.sh'),'a', encoding = 'utf-8') as target:
                    target.write(command + ' # ' + comment + '\n')
                raise Exception("Failed")
            else:
                raise Exception("Use Transmissionrpc to Download")

    def Generate_command(self):
        "Generate the executation command"
        command = "lx download -bt magnet:?xt=urn:btih:%s --continue --output \'%s\'" \
                   % (self.infohash, os.path.join(self.dldir,self.item_key))
        comment = "echo \"%s # %s   %s\" >> taskerror.sh" % (command, self.title, self.PubDate)
        return command, comment

    def Update_main(self):
        try:
            entry_for_db = self.Get_entry()
            self.Update_db(entry_for_db)
            (command, comment) = self.Generate_command()
            if self.IsDownload == True and self.episode != None:
                self.download(command,comment)
                mail['Update'].append({self.item_key:self.team + ", " + str(self.episode)})
                print('Update')
            elif self.IsDownload == False and self.episode != None:
                mail['Update'].append({self.item_key:self.team + ", " + str(self.episode)})
                with open(os.path.join(self.workpath,'lixiantask.sh'),'a', encoding = 'utf-8') as task:
                    task.write(command + ' # ' + comment + '\n')
                print('Update')
            elif self.episode == None:
                mail['Please Check Manually'].append({self.item_key:self.team})
                with open(os.path.join(self.workpath,'taskerror.sh'),'a', encoding = 'utf-8') as task:
                    task.write(command + ' # ' + comment + '\n')
                print('Please Check Manually')
        except Exception as reason:
            if str(reason) == "Premature For Parse":
                print((str(reason)))
            elif str(reason) == "No Update over 9 Days" and self.IsChangeteam:
                print("Try to change team")
                result = self.Update_team()
                if result != None:
                    print("Success. Retry to update")
                    self.Update_main()
                else:
                    print("Failed")
                    mail[str(reason)].append({self.item_key:self.team})
            elif str(reason) in mail:
                print((str(reason)))
                mail[str(reason)].append({self.item_key:self.team})
            else:
                print((Exception), end=' ')
                print((str(reason)))

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
                   r"\d+(?=END|end|End| END| end| End|_END)"
    ]
    for i in expressions:
        numbers = re.findall(i,title)
        if len(numbers) == 1:
            return int(numbers[0])

def update():
    d = Downloader()
    d.init_db_and_task()
    for item_key in list(d.tasks.keys()):
        print(item_key, end=" ")
        entry = Entry(item_key)
        entry.Update_main()
    content = d.Generate_mail()
    print(content)
    if content != '':
        try:
            d.Send_mail(content)
        except:
            pass

def testrss():
    d = Downloader()
    for item_key in list(d.tasks.keys()):
        entry = Entry(item_key)
        if entry.GetFeedinfo() == []:
            print("RSSError %s" % item_key)

def makeup():
    d = Downloader()
    d.init_db_and_task()
    conn = sqlite3.connect(os.path.join(d.workpath,'bangumi.db'))
    cur = conn.cursor()
    if '-wl' in sys.argv:
        whitelist.append(sys.argv[sys.argv.index('-wl')+1])
    for item_key in list(d.tasks.keys()):
        entry = Entry(item_key)
        if whitelist != []:
            if not entry.series in whitelist:
                continue
        else:
            if entry.series in blacklist:
                continue
        if '-net' in sys.argv:
            itemlist = entry.GetFeedinfo()
            if itemlist == []:
                continue
            for epi in itemlist:
                cur.execute('''SELECT * from Updated
                                WHERE title = ? AND infohash = ?;''',(epi['title'],epi['infohash']))
                if cur.fetchone() == None:
                    item = (entry.weekday,entry.series,epi['title'],epi['episode'],epi['PubDate'],entry.team,epi['infohash'])
                    if Cal_timegone(epi['PubDate']) < 90*86400:
                        cur.execute('INSERT INTO Updated VALUES (?,?,?,?,?,?,?)',item)
                        conn.commit()
        if '-db' in sys.argv:
            episodeNums = set()
            for root,dirs,files in os.walk(os.path.join(d.dldir,item_key)):
                for name in files:
                    tmp = Cal_episode(name)
                    if tmp != None:
                        episodeNums.add(int(tmp))
                    else:
                        episodeNums.add(tmp)
            episodeNums.discard(None)
            print(item_key)
            print(episodeNums)
            cur.execute('SELECT title, PubDate, infohash, episode FROM Updated WHERE series = (?);',(entry.series,))
            a = cur.fetchall()
            for i in a:
                entry.title, entry.PubDate, entry.infohash, entry.episode = i
                if entry.episode not in episodeNums:
                    (command, comment) = entry.Generate_command()
                    with open(os.path.join(d.workpath,'lixiantask.sh'),'a', encoding = 'utf-8') as task:
                        task.write(command + ' # ' + comment + '\n')
    conn.close()

def main():
    if len(sys.argv) == 1:
        print_help()
    elif sys.argv[1] == "update":
        update()
    elif sys.argv[1] == "makeup":
        makeup()
    elif sys.argv[1] == "test":
        testrss()
    else:
        print_help()

if __name__ == "__main__":
    main()
