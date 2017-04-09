import re
import os
import logging
import base64
import time
import datetime
import urllib.request, urllib.error, urllib.parse

import requests
import feedparser

from modules.error import RssError

USER_AENT = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, '
             'like Gecko) Chrome/42.0.2311.135 Safari/537.36')

def extract_episode(title):
    """extract episode number from title"""
    expressions = [r"(?<=第)\d+(?=集|话|話|局)",
                   r"(?<=【)\d+(?=】)|(?<=\[)\d+(?=\])",
                   r"(?<= )\d+(?= )",
                   r"(?<=- )\d+",
                   r"\d+(?=[v|V]\d{1})",
                   r"\d+\.5",
                   r"\d+(?=END|end|End| END| end| End|_END)"]
    for i in expressions:
        numbers = re.findall(i,title)
        if len(numbers) == 1:
            if re.match(r"\d+\.5",numbers[0]):
                return float(numbers[0])
            else:
                return int(numbers[0])

def to_iso_utc(date_string, format):
    d = datetime.datetime.strptime(date_string, format)
    return time.strftime("%Y-%m-%d %H:%M:%SZ", d.utctimetuple())

def parse_feed(url,set_user_agent=True,httpproxy=None):
    if httpproxy == None:
        handlers = None
    else:
        proxy = urllib.request.ProxyHandler( {"https":httpproxy} )
        handlers = [proxy]
    if set_user_agent == True:
        feedparser.USER_AGENT = USER_AENT
    feed = feedparser.parse(url,handlers=handlers)
    if feed.entries == []:
        raise RssError
    return feed

def parse_page(url,set_user_agent=True,httpproxy=None):
    if httpproxy == None:
        proxies = None
    else:
        proxies = {'http': 'http://' + httpproxy,
                'https': 'http://' + httpproxy}
    if set_user_agent == True:
        headers = { 'User-Agent' : USER_AENT }
    else:
        headers = None
    page = requests.get(url, headers=headers, proxies=proxies)
    return page
