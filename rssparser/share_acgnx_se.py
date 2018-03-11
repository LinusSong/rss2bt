from rssparser.tackles import extract_episode, parse_feed, to_iso_utc

def get_entries(url,source,weekday,series,team,httpproxy=None):
    "The function is used to parse feed and extract information"
    feed = parse_feed(url, set_user_agent=True, httpproxy=httpproxy)
    entries = []
    for i in feed.entries:
        entries.append({
            'source':source,
            'weekday':weekday,
            'series':series,
            'team':team,
            'title': i.title,
            'page_link': i.link,
            'pubdate': to_iso_utc(i.published,"%a, %d %b %Y %H:%M:%S %z"),
            'episode': extract_episode(i.title),
            'download_link': i.enclosures[0].href,
            'link_type': 'magnet'
            })
    return entries
