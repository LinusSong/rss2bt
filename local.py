#-*-coding:utf-8 -*-
import transmissionrpc
import time

tc = transmissionrpc.Client('localhost',port=9091,user='your_username11@',password='your_password11@')
need_remove = []
for tid in tc.info():
    if tc.info()[tid].progress == 100.0 and (tc.info()[tid].uploadRatio > 1 or time.time() - tc.info()[tid].doneDate > 300):
        need_remove.append(tid)
for tid in need_remove:
    tc.remove_torrent(tid)
