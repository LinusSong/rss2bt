from modules.module import merge_args_yaml, Item, get_source_from_rss
from modules.error import RssError
from operator import itemgetter

def testrss(args):
    config = merge_args_yaml(args)
    for item_key in config['tasks']:
        e = Item(config,item_key)
        if config['chosenitem']:
            if e.series not in config['chosenitem']:
                continue
        print('%s' % (item_key,))
        latest_episode_each_team = []
        for team in config['tasks'][item_key]['rss']:
            try:
                e.team = team
                e.rss = config['tasks'][item_key]['rss'][team]
                e.source = get_source_from_rss(e.rss)
                entries = e.get_entries()
                for entry in entries:
                    if entry['episode']:
                        latest_episode_each_team.append({'team':team,
                            'episode':entry['episode'],
                            'pubdate':entry['pubdate'],
                            })
                        break
            except RssError:
                print("RssError %s, %s" % (item_key,team))
        episodes = [i['episode'] for i in latest_episode_each_team]
        if episodes == []:
            print("Error: 出现错误，请自行查看")
            continue
        maxepisode = max(episodes)
        fastteams = [i for i in latest_episode_each_team if i['episode']==maxepisode]
        sorted_fastteams = sorted(fastteams,key=itemgetter('pubdate'))
        fastest = sorted_fastteams[0]
        print("    最佳推测: %s，最新剧集: %s" % (fastest['team'],fastest['episode']))
        if len(sorted_fastteams) > 1:
            print("    其他选择: %s" % ('，'.join([i['team'] for i in sorted_fastteams[1:]],)))
