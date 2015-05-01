#-*-coding:utf-8 -*-

import re
import os
import time
import rss2lx_db
import rss2lx_network
from openpyxl import load_workbook
from openpyxl import Workbook

def mkdir(path,info):
    infolist = info + '.list'
    if os.path.isfile(path+infolist) == False:
        temp = open(path+infolist,'w')
        temp.close()
    if os.path.exists(path+info) == False:
        os.makedirs(path+info)

def dlCriterion(timestr):
    try:
        a = time.mktime(time.strptime(timestr, "%a, %d %b %Y %H:%M:%S +0800"))
    except:
        a = time.mktime(time.strptime(timestr, '%Y/%m/%d %H:%M'))
    b = time.time()
    timegone = b -a
    print timegone
    
def Task(infolist, itemTitle):
    normal = ("lx download -bt magnet:?xt=urn:btih:" + infohash + 
                " --continue --output '" + path + itemTitle + "/'")
    newitem = infolist[0] + ' || ' + infolist[1] + ' || ' + infolist[2]
    print newitem
    error = "echo \"" + normal + " # " + newitem + "\" >> taskerror.sh"
    execute = normal + ' || ' + error + '\n'
    return execute

def readConfig():
    try:
        a = open(rss2lx.config)
        path = a. readline()
        username = a. readline()
        password = a. readline()
        Proxy = a. readline()
        if path == '':
            path = './'
        if list(path)[-1] <> '/':
            path += '/'
    except:
        path = './'
        username = password = Proxy = ''
    return path, username, password, Proxy

def main(path, username, password, Proxy):
    task = open('lixiantask.sh','w')
    task.write('#!/bin/sh'+'\n')
    wbpath = path + 'bangumi.xlsx'
    wb = load_workbook(wbpath)
    feedlist = rss2lx_db.ConvFeedlist(wb)
    CheckWs(feedlist, wb)
    mailcontent = ''
    for item in feedlist:
        itemTitle = item[0]
        itemRss = item[1]
        lastTitle, lastPubDate = QueryItem(wb[itemTitle])
        mkdir(path, itemTitle)
        if dlCriterion(lastPubDate) <= 572400: 
            continue
        infolist, mailadded = rss2lx_network.CatchFeedinfo(item, Proxy, itemRss)
        mailcontent += mailadded
        if infolist[1] = '' or dlCriterion(infolist[1]) < 5400:
            continue
        if lastTitle <> infolist[0]:
            rss2lx_db.appendEntry(wb, itemTitle, infolist)
            rss2lx_db.updateBan(wb, infolist)
            execution = Task(infolist, itemTitle)
            task.write(execution)
        elif dlCriterion(lastPubDate) >= 777600:
            mailcontent += "No update for over 9 days————" + item + '\n'
    if listformail <> '':
        try:
            mail(username, password, mailcontent)
        except:
            print "Fail to send mail"
    wb.save(wbpath)

main(readConfig())
