#!python3
import logging
import argparse
import os

from subcommands.checkup import checkup
from subcommands.testrss import testrss
from subcommands.update import update
from modules.global_var import WORKPATH

logging.basicConfig(filename=os.path.join(WORKPATH,'log.log'),
                    format='%(asctime)s %(message)s',
                    level=logging.WARNING)

"""
整体设计思路说明:
1. 关键参数:
    entry   type: dict
            example: {'source' 'TEXT','weekday':'TEXT','series':'TEXT',
                      'title':'TEXT','episode':'INTEGER','pubdate':'TEXT',
                      'team':'TEXT','download_link':'TEXT','link_type':'TEXT',
                      'page_link':'TEXT'}
            必须完全符合范例。只允许episode为None。
            复数形式: entries   type: list
            主要输入输出: parser的输出(entries),
                        datebase模块里的输入输出
                        select_entries_needed的输入

    config  type： dict
            所有配置都写在同一个dict里面。
            任何配置的输入均通过它

2. update关键步骤
    获得config
    初始化task文件和db，建立EmailSender实例
    对于tasks里的每一个item，建一个Item实例，通过get_entries_needed获得需要下载的
    entries，将输出记入EmailSender，然后转入download进行下载
    最后EmailSender整理并发送email
"""

def parse_args_cli():
    """Parses the arguments from command line input.

      The usage of commands are detailed listed in the help text. Here is the
    overview of the function.

    Args:
        main.py [-v] [-h] [-cg CONFIG_GLOBAL] [-ck CONFIG_TASKS]
               [-dp DOWNLOAD_PATH] [-hp HTTPPROXY]
               [-eu EMAIL_USERNAME] [-ep EMAIL_PASSWORD] [-er EMAIL_RECEIVER]
               [-ts TRANSMISSIONRPC_SERVER] [-tu TRANSMISSIONRPC_USER]
               [-tp TRANSMISSIONRPC_PASSWORD]
               [-td TRANSMISSIONRPC_DOWNLOAD_PATH]

        general includes two common arguments,'-h'(help), '-v'(version) and a
                special one, '-c'(config). The default value for '-c' is
                'config.yml' in the same path of the main.py.
        config  in addtion, all arguments in config file except tasks can be
                modified in the command lines.

        There are three allowable subcommands: update, checkup and testrss.

        update  [-h] [-w REDUCEDINTERVALS | -nw] [-d [{bt,xl}]]
                the reducedintervals means how many days early to parse
                feed(default: 0.325days) and nowaiting means ignoring update
                intervals and parsing feed immediately, while the '-d' set the
                download method(default is bt, and another way is xl.)

        checkup [-h] [-nt] [-db] [-i CHOSENITEM [CHOSENITEM ...]]
                three arguments are used. The usenet means scanning all rss url
                in the config file and writing them into datebase, as well as
                the usedatebase means comparing the datebase and the files that
                have been downloaded and generating a log file with the
                undownloaded files.The chosenitem is whitelist, and only the
                items of it will be checked.

        testrss [-h] [-i CHOSENITEM [CHOSENITEM ...]]
                no optional arguments.

    Returns:
        args    the NameSpace class will be returned directly. Remember that
                the args.func is included.

        list of args:
                general: func, config, [args in config if there are not None]
                update: waitingdays, downloadmethod
                checkup: usenet, usedatebase
                testrss

    Raises:
        No extra exceptions but the default exceptions from argparse module.
    """

    parser = argparse.ArgumentParser(
        add_help=False,
        argument_default=argparse.SUPPRESS,
        description="parse magnet link from rss and download.")

    subparsers = parser.add_subparsers(title='commands', metavar='',
        help='use -h to show the detail help text')

    parser_update = subparsers.add_parser('update', aliases='u',
        help='update the datebase and download')
    group = parser_update.add_mutually_exclusive_group()
    group.add_argument('-w', dest='reducedintervals',
        type=float, default=0.325,
        help='how many days early to parse feed(default: 0.325days)')
    group.add_argument('-nw', '--nowaiting', action="store_true",
        help='no waiting days before parsing feed')
    parser_update.add_argument('-d', '--downloadmethod',
        nargs="?", const='bt', choices=['bt','xl','aria2'], default='bt',
        help='download by transmissionrpc or aria2 after parsing magnet'
             ' or create xunlei-lixian script')
    parser_update.set_defaults(func=update)

    parser_checkup = subparsers.add_parser('checkup', aliases='c',
        help='check up the datebase and update throughtly')
    parser_checkup.add_argument('-nt', '--usenet', action="store_true",
        help='parse all rss lists and update the datebase')
    parser_checkup.add_argument('-db', '--usedatebase', action="store_true",
        help='scan datebase and download no-beginning items')
    parser_checkup.add_argument('-i', '--chosenitem', nargs='+',
        help='the checkup action only contains the chosen item')
    parser_checkup.set_defaults(func=checkup)

    parser_testrss = subparsers.add_parser('testrss', aliases='t',
        help='test all rss')
    parser_testrss.add_argument('-i', '--chosenitem', nargs='+',
        help='the checkup action only contains the chosen item')
    parser_testrss.set_defaults(func=testrss)

    group_general = parser.add_argument_group('general arguments')
    group_general.add_argument('-v', '--version',
        action='version', version='1.0',
        help='show the version and exit')
    group_general.add_argument('-h', '--help',
        action='help',
        help='show this help message and exit')
    group_general.add_argument('-cg', dest='config_global',
        default=os.path.join(WORKPATH, 'config_global.yml'),
        help='use an existing configuaration file'
             '(default:config_global.yml in the program path)')
    group_general.add_argument('-ct', dest='config_tasks',
        default=os.path.join(WORKPATH, 'config_tasks.yml'),
        help='use an existing configuaration file'
             '(default:config_tasks.yml in the program path)')

    group_config = parser.add_argument_group('config arguments')
    group_config.add_argument('--download_path', dest='download_path')
    group_config.add_argument('-hp', dest='httpproxy')
    group_config.add_argument('-eu', dest='email_username')
    group_config.add_argument('-ep', dest='email_password')
    group_config.add_argument('-er', dest='email_receiver')
    group_config.add_argument('-ts', dest='transmissionrpc_server')
    group_config.add_argument('-tu', dest='transmissionrpc_user')
    group_config.add_argument('-tp', dest='transmissionrpc_password')
    group_config.add_argument('-td', dest='transmissionrpc_download_path')
    group_config.add_argument('-ar', dest='aria2_rpc')
    group_config.add_argument('-ad', dest='aria2_download_path')

    args = parser.parse_args()
    logging.info(args)
    return args

def main():
    args = parse_args_cli()
    args.func(args)

if __name__ == "__main__":
    main()
