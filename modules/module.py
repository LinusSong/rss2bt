import base64
import datetime
import json
import os
import re
import sys
import time

import requests
import transmissionrpc
import yaml

from rssparser.parser import get_entries
from modules.datebase import *
from modules.global_var import *
from modules.error import TransmissionrpcError, Aria2Error

def merge_args_yaml(args):
    """Merges arguments from parse_args_cli and config.yml.

    This function intends to avoid repetitve operations when creating class
    Downloader and its subclass.
    The arguments from parse_args_cli will overwrite that from config.yaml.

    Args:
        args    the values returned by parse_args_cli

    Returns:
        config  a dict made of merged arguments.
        list of config dict:
            #TODO
            download_path
            httpproxy
            email_username
            email_password
            email_receiver
            transmissionrpc_server
            transmissionrpc_user
            transmissionrpc_password
            transmissionrpc_download_path

    """

    config_yaml = yaml.load(open(args.config_global,encoding='utf-8').read())
    config = config_yaml.copy()
    config.update(vars(args))
    del config['func']
    del config['config_global']
    del config['config_tasks']
    config['tasks'] = yaml.load(open(args.config_tasks,encoding='utf-8').read())
    if config['httpproxy'].lower() == 'none':
        config['httpproxy'] = None
    if os.path.exists(config['download_path']) == False:
        config['download_path'] = os.path.join(os.path.expanduser('~'),'Downloads','bangumi')
    return config

def calculate_timegone(timestr):
    """calculate how long time has gone from timestr to now.

    Args:
        timestr timestr is one of values returned by parse_module, which
                format must be '%Y-%m-%d %H:%M:%SZ'.

    Returns:
        time_gone   the seconds that has gone from timestr to now.
    """

    d = datetime.datetime.strptime(timestr, '%Y-%m-%d %H:%M:%SZ')
    a = datetime.datetime.utcnow()- d
    time_gone = a.total_seconds()
    return time_gone

def initialize_tasks():
    with open(TASKS,'w',encoding='utf-8') as t:
        pass

def get_source_from_rss(rss):
    if rss.find('https://bangumi.moe/rss/tags') == 0:
        source = 'bangumi_moe'
    elif rss.find('https://share.dmhy.org/topics/rss/rss.xml?keyword=') == 0:
        source = 'share_dmhy_org'
    elif rss.find('https://open.acgnx.se/rss-search=') == 0:
        source = 'share_acgnx_se'
    elif rss.find('https://share.xfsub.com/') == 0:
        source = 'share_xfsub_com'
    else:
        raise Exception
    return source

def careful_print(s):
    t = sys.stdout.encoding
    b = s.encode(t,'ignore').decode(t)
    print(b)

class Item(object):
    def __init__(self, config, item_key):
        self.config = config
        self.item_key = item_key
        self.update_interval = config['tasks'][item_key]['update_interval']
        self.team = config['tasks'][item_key]['team']
        if self.team:
            self.rss = config['tasks'][item_key]['rss'][self.team]
            self.source = get_source_from_rss(self.rss)
        self.weekday = item_key[:3]
        self.series = item_key[4:]

    def get_entries(self):
        entries = get_entries(self.rss,self.source,self.weekday,self.series,
            self.team,httpproxy=self.config['httpproxy'])
        return entries

    def get_entries_needed(self):
        """

        Return:
            entries_needed
            flag            type: string
                            reason
        """
        flag = None
        entries_needed = []
        latest_entry_db = query_latest_by_series(self.series)
        if latest_entry_db == None:
            pass
        elif (calculate_timegone(latest_entry_db['pubdate']) <=
            (self.update_interval-self.config['reducedintervals'])*86400):
            flag = 'skipped'
            return entries_needed, flag
        entries = self.get_entries()
        for i in entries:
#条件：entry可提取集数，发布时间超过一小时,集数大于数据库里最新一集
#由于latest_entry_db可能为None，故单列最后一条
#新增条件：去重复剧集的任务交给这边，方法是选择发布晚的那一集，不看简繁
            if (i['episode'] != None and
                3600 <= calculate_timegone(i['pubdate']) <= 90*86400 and
                (latest_entry_db == None or
                i['episode'] > latest_entry_db['episode']) and
                i['episode'] not in [x['episode'] for x in entries_needed]):
                    entries_needed.append(i)
        if entries_needed == []:
            if (latest_entry_db != None and
                calculate_timegone(latest_entry_db['pubdate']) >= 9*86400):
                flag = 'no update over 9 days'
            else:
                flag = 'not yet updated'
        return entries_needed, flag

    def download_aria2(self,entry):
#此处不能使用os.path.join，否则Windows上会使用'\\'，而不是'/'
        dldir = self.config['aria2_download_path'] + '/' + self.item_key
        aria2_rpc = self.config['aria2_rpc']
        tmp = re.match('http(s?)://token:(.*)@(.*)/jsonrpc',aria2_rpc)
        if tmp:
            https_tag, token, ip_port = tmp.groups()
            aria2_rpc = 'http' + https_tag + '://' + ip_port + '/jsonrpc'
        elif re.match('http(s?)://(.*)/jsonrpc',aria2_rpc):
            token = None
        else:
            raise Aria2Error
        if token:
            payload = [{
            	'jsonrpc': '2.0',
            	'id': 1,
            	'method': 'aria2.addUri',
            	'params': ['token:'+token, [entry['download_link']], {'dir':dldir}]
            	}]
        else:
            payload = [{
            	'jsonrpc': '2.0',
            	'id': 1,
            	'method': 'aria2.addUri',
            	'params': [[entry['download_link']], {'dir':dldir}]
            	}]
        response = requests.post(aria2_rpc, data=json.dumps(payload))
        if not response.ok:
            raise Aria2Error

    def download_bt(self,entry):
        tc = transmissionrpc.Client(
            self.config['transmissionrpc_server'],
            port=9091,
            user=self.config['transmissionrpc_user'],
            password=self.config['transmissionrpc_password']
            )
#此处不能使用os.path.join，否则Windows上会使用'\\'，而不是'/'
        dldir = self.config['transmissionrpc_download_path'] + '/' + self.item_key
        if entry['link_type'] == 'magnet':
            tr = tc.add_torrent(entry['download_link'], download_dir=dldir)
        elif entry['link_type'] == 'torrent':
            data = parse_page(entry['download_link'],httpproxy=self.config['httpproxy'])
            torrent = base64.b64encode(date.content.decode('utf-8'))
            tr = tc.add_torrent(torrent, download_dir=dldir)

    def write_sh(self,entry):
        url = entry['download_link']
        if entry['link_type'] == 'magnet':
            url = url[:url.find('&')]
        with open(TASKS,'a',encoding='utf-8') as t:
            t.write(url + ' # ' + entry['title'] + '\n')

    def download(self,entry):
        if self.config['downloadmethod'] == 'bt':
            try:
                self.download_bt(entry)
            except:
                raise TransmissionrpcError
        elif self.config['downloadmethod'] == 'xl':
            self.write_sh(entry)
        elif self.config['downloadmethod'] == 'aria2':
            self.download_aria2(entry)
