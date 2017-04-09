from modules.module import *
from modules.datebase import *
from parser.tackles import extract_episode
def checkup(args):
    config = merge_args_yaml(args)
    initialize_db()
    initialize_tasks()
    for item_key in config['tasks']:
        item = Item(config,item_key)
        if config['chosenitem'] != None:
            if not item.series in config['chosenitem']:
                continue
        if config['usenet']:
            entries = item.get_entries()
            for entry in entries:
                if not has_entry(entry) and calculate_timegone(entry['pubdate']) < 90*86400:
                    if entry['episode'] != None:
                        update_db(entry)
                    else:
                        item.write_sh(entry)

        if config['usedatebase']:
            episode_nums = set()
            for root,dirs,files in os.walk(os.path.join(config['download_path'],item_key)):
                for name in files:
                    episode_nums.add(extract_episode(name))
            episode_nums.discard(None)
            print(item_key,episode_nums)
            entries = query_all_by_series(item.series)
            for entry in entries:
                if entry['episode'] not in episode_nums:
                    item.write_sh(entry)
