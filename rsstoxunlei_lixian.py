#-*-coding:utf-8 -*-
import re
import os
import urllib
import urllib2
import feedparser
import time
if os.path.exists('/home/l/') == True:
    prepath = '/home/l/'
else:
    prepath = '/mnt/sda1/'
feedlistfile = open(prepath + 'feedlist.txt','r+')  #首先有一个叫feedlist.txt的文件，每行格式为"xx动漫:rss地址"
feedlistcontent = feedlistfile.read().split('\n')         #分成一个叫feedlistcontent的表
task = open(prepath + 'lixiantask.sh','w')            #任务另写入一个叫lixiantask.sh的地方来执行
task.write('#!/bin/sh'+'\n')
feedlistfile.close()
feedlistcontent.pop(-1)
for i in feedlistcontent:
    feedaddress = i[i.find(":") + 1:]           #这部动漫的RSS地址
#    print feedaddress
    listfile = i[:i.find(":")]                  #这部动漫的名字
#    print listfile
    listfilename = listfile + '.list'
#    print listfilename
    if os.path.isfile(prepath+listfilename) == False:   #检查下这部动漫是否有单独的列表文件，没有则建立
        temp = open(prepath+listfilename,'w')
        temp.close()
    sql =open(prepath+listfilename,'r+')                #打开表
    sqllist = sql.read().split('\n')            
    if len(sqllist) > 1:
        sqllist.pop(-1)                             #这会去掉最后那个空的元素
    feedparser.USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36"
    feedcontent = feedparser.parse(feedaddress) #读取RSS内容
#    print feedcontent
    itemtitle = feedcontent.entries[0].title.encode('utf8')
#    print itemtitle
    if sqllist[-1] <> itemtitle:
        # 下面几行是为了实现读取infohash
        feedlink = feedcontent.entries[0].link
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36'
        values = {'name' : 'REsdds',
                  'location' : 'Shanghai',
                  'language' : 'q=0.8,zh-CN' }
        headers = { 'User-Agent' : user_agent }
        data = urllib.urlencode(values)
        req = urllib2.Request(feedlink, data, headers)
        response = urllib2.urlopen(req)
        the_page = response.read()
        # 下面是为了获取infohash
        a1 = re.findall('<p><strong>會員專用連接:</strong>&nbsp;<a href="[^\s]*\.torrent">',the_page)
        a2 = re.findall('//[^\s]*\.torrent',a1[0])
        infohash = a2[0][25:65]
        # 下面是为了获取发布时间已经过去多少
        a1 = re.findall('<li>發佈時間: <span>[^<]*</span></li>',the_page)
        a2 = re.findall('<span>[^<]*</span>',a1[0])
        a3 = a2[0].find('</span>')
        feedtime = a2[0][6:a3]
        feedtime = time.mktime(time.strptime(feedtime, '%Y/%m/%d %H:%M'))
        timegone = time.time() - feedtime
        #下面是为了获取体积大小
        a1 = re.findall('<li>文件大小: <span>[^<]*</span></li>',the_page)
        a2 = re.findall('<span>[^<]*</span>',a1[0])
        a3 = a2[0].find('</span>')
        filesize = a2[0][6:a3]
        if filesize[-2:] = 'GB':
            multiplier = 1024
        elif filesize[-2:] = 'MB':
            multiplier = 1
        elif filesize[-2:] = 'KB':
            multiplier = 0.001
        size = float(filesize[:-2]) * multiplier
#        print os.path.exists('/mnt/sda1/'+listfile)
        if os.path.exists(prepath+listfile) == False:
            os.makedirs(prepath+listfile)
        if timegone >= 5400 and size < 500:      #写入条件为发布一个半小时以及体积小与500MB
            sql.write(itemtitle)                    
            sql.write('\n')
            if os.path.exists('/home/l/') == True:
                execution = 'lx download -bt magnet:?xt=urn:btih:' + infohash + ' --output ' + prepath + listfile + '/' 
            else:
                execution = 'python /root/xunlei-lixian-master/lixian_cli.py download -bt magnet:?xt=urn:btih:' + infohash + ' --output ' + prepath + listfile + '/' 
            #注意此处有个bug，如果下载工具要设置为aria2，这里最后一个 + '/'必须去掉
            task.write(execution+'\n')
#        os.system('python /root/xunlei-lixian-master/lixian_cli.py download -bt magnet:?xt=urn:btih:' + infohash + ' --output /mnt/sda1/' + listfile)   #执行离线下载