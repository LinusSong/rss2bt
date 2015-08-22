#-*-coding:utf-8 -*-
from update import Downloader, Entry, Cal_timegone, Cal_episode
import sqlite3
import os
import sys

blacklist = ['食戟之靈','悠哉日常大王Repeat','偶像大師灰姑娘女孩Ⅱ','ToLoveRuDarkness2nd','魔法少女☆伊莉雅2weiHerz!']
whitelist = []

def main():
    d = Downloader()
    d.init_db_and_task()
    conn = sqlite3.connect(os.path.join(d.workpath,'bangumi.db'))
    cur = conn.cursor()
    if '-w' in sys.argv:
        whitelist.append(sys.argv[sys.argv.index('-w')+1])
    for item_key in d.tasks.keys():
        entry = Entry(item_key)
        if whitelist != []:
            if not entry.series.encode('utf-8') in whitelist:
                continue
        else:
            if entry.series.encode('utf-8') in blacklist:
                continue
        if 'net' in sys.argv:
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
        if 'db' in sys.argv:
            episodeNums = set()
            for root,dirs,files in os.walk(os.path.join(d.dldir,item_key)):
                for name in files:
                    tmp = Cal_episode(name)
                    if tmp != None:
                        episodeNums.add(int(tmp))
                    else:
                        episodeNums.add(tmp)
            episodeNums.discard(None)
            print item_key, episodeNums
            cur.execute('SELECT title, PubDate, infohash, episode FROM Updated WHERE series = (?);',(entry.series,))
            a = cur.fetchall()
            for i in a:
                entry.title, entry.PubDate, entry.infohash, entry.episode = i
                if entry.episode not in episodeNums:
                    (command, comment) = entry.Generate_command()
                    with open(os.path.join(d.workpath,'lixiantask.sh'),'a') as task:
                        task.write(command + ' # ' + comment + '\n')
    conn.close()

if __name__ == '__main__':
    main()
