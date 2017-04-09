from modules.module import merge_args_yaml, Item

def testrss(args):
    config = merge_args_yaml(args)
    for item_key in config['tasks']:
        e = Item(item_key, config)
        try:
            e.get_entries_needed()
        except RssError:
            print("RSSError %s" % item_key)
