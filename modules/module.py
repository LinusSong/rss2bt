import os
import base64
import time

import transmissionrpc
import yaml

from parser.parser import get_entries
from modules.datebase import *
from modules.global_var import *
from modules.error import TransmissionrpcError

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

    config_yaml = yaml.load(open(args.config,encoding = 'utf-8').read())
    config = config_yaml.copy()
    config.update(vars(args))
    del config['func']
    del config['config']
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

    time_seconds = time.mktime(time.strptime(timestr,'%Y-%m-%d %H:%M:%SZ'))
    time_gone = time.mktime(time.gmtime()) - time_seconds
    return time_gone

def initialize_tasks():
    with open(TASKS,'w',encoding='utf-8') as t:
        t.write('#!/bin/sh'+'\n')

class Item(object):
    def __init__(self, config, item_key):
        self.config = config
        self.item_key = item_key
        self.source = config['tasks'][item_key]['source']
        self.update_interval = config['tasks'][item_key]['update_interval']
        self.team = config['tasks'][item_key]['team']
        self.rss = config['tasks'][item_key]['rss'][self.team]
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
            flag = 'premature for download'
            return entries_needed, flag
        entries = self.get_entries()
        for i in entries:
#条件：entry可提取集数，发布时间超过一小时,集数大于数据库里最新一集
#由于latest_entry_db可能为None，故单列最后一条
            if (i['episode'] != None and
                calculate_timegone(i['pubdate']) >= 3600 and
                (latest_entry_db == None or
                i['episode'] > latest_entry_db['episode'])):
                    entries_needed.append(i)
        if entries_needed == []:
            if (latest_entry_db != None and
                calculate_timegone(latest_entry_db['pubdate']) >= 9*86400):
                flag = 'no update over 9 days'
            else:
                flag = 'not yet updated'
        return entries_needed, flag

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
        dldir = os.path.join(self.config['download_path'],self.item_key)
        if os.path.exists(dldir) == False:
            os.makedirs(dldir)
        if self.config['downloadmethod'] == 'bt':
            try:
                print("try transmissionrpc")
                self.download_bt(entry)
            except:
                raise TransmissionrpcError
            else:
                print("Use Transmissionrpc to Download")
        elif self.config['downloadmethod'] == 'xl':
            self.write_sh(entry)
