import re
from bs4 import BeautifulSoup

from parser.tackles import extract_episode, parse_page, to_iso_utc

def get_entries(url,source,weekday,series,team,httpproxy=None):
    page = parse_page(url, set_user_agent=True, httpproxy=httpproxy)
    entries = []
    soup = BeautifulSoup(page.content, 'html.parser')
    items = soup.find('tbody',id='data_list').find_all('tr')
    for i in items:
        title = i.find('td',style="text-align:left;").text.strip()
        download_link = i.find('td',style="text-align:left;").a['href']
        datetuple = re.search('(\w{4})/(\w{2})/(\w{2})',download_link).groups()
        timetuple = re.search('(\w{2}):(\w{2})',
            i.find_all('td')[-1].text).groups()
        pubdate_local = "%s %s:00 +0800" % (' '.join(reversed(datetuple)),
            ':'.join(timetuple))
        entries.append({
            'source':source,
            'weekday':weekday,
            'series':series,
            'team':team,
            'title': title,
            'page_link': ('http://share.xfsub.com:88/' +
                i.find('a',target="_blank")['href']),
            'pubdate': to_iso_utc(pubdate_local,"%d %m %Y %H:%M:%S %z"),
            'episode': extract_episode(title),
            'download_link': download_link,
            'link_type': 'torrent'
            })
    return entries
