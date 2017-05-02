import logging

from modules.module import *
from modules.datebase import *
from modules.email import EmailSender
from modules.error import RssError, TransmissionrpcError

def update(args):
    config = merge_args_yaml(args)
    initialize_tasks()
    initialize_db()
    emailsender = EmailSender(config)
    for item_key in config['tasks']:
        print(item_key)
        item = Item(config, item_key)
        try:
            entries_needed, flag = item.get_entries_needed()
        except RssError:
            logging.error(item_key)
        if flag == None:
            for entry in entries_needed:
                print("    " + entry['title'])
                try:
                    item.download(entry)
                except TransmissionrpcError:
                    logging.error(item_key,entry)
                else:
                    update_db(entry)
            emailsender.add_text(item_key,entries=entries_needed)
        else:
            emailsender.add_text(item_key,flag=flag)
    email_text = emailsender.compile_mail()
    print(email_text)
    emailsender.send_mail(email_text)
