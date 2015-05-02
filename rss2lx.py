#-*-coding:utf-8 -*-

import re
import os
import time
import rss2lx_db
import rss2lx_network
from openpyxl import load_workbook
from openpyxl import Workbook

def mkdir(dldir,info):
    if os.path.exists(dldir+info) == False:
        os.makedirs(dldir+info)

def dlCriterion(timestr):
    if timestr <> '':
        b = time.time()
        try:
            a = time.mktime(time.strptime(timestr, "%a, %d %b %Y %H:%M:%S +0800"))
        except:
            a = time.mktime(time.strptime(timestr, '%Y/%m/%d %H:%M'))
        timegone = b -a
    else:
        timegone = 600000 
    return timegone
    
def Task(infolist):
    normal = ("lx download -bt magnet:?xt=urn:btih:" + infolist[2] + 
                " --continue --output '" + dldir + 
                infolist[0].encode('utf8') + "/'")
    newitem = (infolist[0].encode('utf8') + ' || ' + 
               infolist[1].encode('utf8') + ' || ' + infolist[2])
    error = "echo \"" + normal + " # " + newitem + "\" >> taskerror.sh"
    execute = normal + ' || ' + error + '\n'
    return execute

def readConfig():
    try:
        Config = open(os.path.expanduser('~') + '/rss2lx.config').read()
        Configlist = Config.split('\n')
        Configlist.pop(-1)
        dldir = Configlist[0]
        username = Configlist[1]
        password = Configlist[2]
        Proxy = Configlist[3]
        if dldir == '':
            dldir = os.path.expanduser('~')
        if list(dldir)[-1] <> '/':
            dldir += '/'
    except:
        dldir = './'
        username = password = Proxy = ''
    return dldir, username, password, Proxy

def main(dldir, username, password, Proxy):
    task = open(os.path.expanduser('~') + '/lixiantask.sh','w')
    task.write('#!/bin/sh'+'\n')
    wbpath = dldir + 'feedlist.xlsx'
    wb = load_workbook(wbpath)
    feedlist = rss2lx_db.ConvFeedlist(wb)
    rss2lx_db.CheckWs(feedlist, wb)
    mailcontent = ''
    for item in feedlist:
        lastTitle, lastPubDate = rss2lx_db.QueryItem(wb[item[0]])
        mkdir(dldir, item[0])
        if dlCriterion(lastPubDate) <= 572400: 
            continue
        infolist = rss2lx_network.CatchFeedinfo(item[1], Proxy)
        if infolist[0] == '':
            mailcontent += ("Wrong RSS or banned————" + 
                            item[0] + ':' + item[1] + '\n')
            continue
        if dlCriterion(infolist[1]) < 5400:
            continue
        if lastTitle <> infolist[0]:
            mailcontent += (infolist[0].encode('utf8') + ' ' + 
                            infolist[1].encode('utf8') + '\n')
            print infolist[0]
            rss2lx_db.appendEntry(wb, item[0], infolist)
            rss2lx_db.appendEntry(wb, "Latest", infolist)
            execution = Task(infolist)
            task.write(execution)
        elif dlCriterion(lastPubDate) >= 777600:
            mailcontent += ("No update for over 9 days————" + 
                            item[0] + ':' + item[1] + '\n')
    if mailcontent <> '':
        print mailcontent
#        try:
        rss2lx_network.mail(username, password, mailcontent)
#        except:
#            print "Fail to sand mail"
    wb.save(wbpath)
    
dldir, username, password, Proxy = readConfig()
main(dldir, username, password, Proxy)
