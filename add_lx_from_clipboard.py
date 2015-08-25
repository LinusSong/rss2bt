#-*-coding:utf-8 -*-
import os
import xerox
import base64

magnet = xerox.paste()
infohash = base64.b16encode(base64.b32decode(magnet[20:52])).lower()
os.system('lx d ' + infohash + ' --continue')
