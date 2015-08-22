#-*-coding:utf-8 -*-
import os
import re
import xerox
import transmissionrpc

from update import Downloader

d = Downloader()
magnet = xerox.paste()
if re.match('[a-f0-9]{40}',magnet) != None:
    magnet = "magnet:?xt=urn:btih:" + magnet
if re.match('magnet:\?xt=urn:btih:.*',magnet) != None:
    tc = transmissionrpc.Client(d.transmissionrpc_server,port=9091,user=d.transmissionrpc_user,password=d.transmissionrpc_password)
    tr = tc.add_torrent(magnet,download_dir=os.path.join(d.transmissionrpc_download_path).encode('utf-8'))
else:
    print "Invalid magnet_link"
