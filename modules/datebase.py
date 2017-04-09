import os
import sqlite3
from modules.global_var import DATEBASE

def initialize_db():
    """若没有数据库，则建立之
    数据库结构由此规定
    """
    with sqlite3.connect(DATEBASE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master where type='table';")
        tables = cur.fetchall()
        if ('updates',) not in tables:
            cur.execute('''CREATE TABLE updates (
                        source TEXT,
                        weekday TEXT,
                        series TEXT,
                        title TEXT,
                        episode INTEGER,
                        pubdate TEXT,
                        team TEXT,
                        download_link TEXT,
                        link_type TEXT,
                        page_link TEXT
                        );'''
                        )
            conn.commit()

def query_column_names():
    """查询表updates的column names, 以便其他函数中生成entry

    Returns:
        list of column names

    """
    with sqlite3.connect(DATEBASE) as conn:
        cur = conn.cursor()
        cur.execute('PRAGMA table_info(updates)')
        t = cur.fetchall()
        column_names = [i[1] for i in t]
    return column_names

def query_latest_by_series(series):
    """根据参数series来获得数据库中的最新一集的完整entry

    Args:
        series  type: string

    Return:
        entry   type: dict
                if there is latest entry
        None    if no entries.
    """
    with sqlite3.connect(DATEBASE) as conn:
        cur = conn.cursor()
        cur.execute('SELECT *,max(pubdate)'
            'FROM updates WHERE series=?;',(series,))
        t = cur.fetchone()
        if t[0]:
            column_names = query_column_names()
            return dict(zip(column_names,t[:-1]))
        else:
            return None

def query_all_by_series(series):
    """根据参数series来获得数据库中的所有的完整entry

    Args:
        series  type: string

    Return:
        entries type: list
                list of entries
    """
    with sqlite3.connect(DATEBASE) as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM updates WHERE series=?;',(series,))
        t = cur.fetchall()
        if t:
            column_names = query_column_names()
            return [dict(zip(column_names,i)) for i in t]
        else:
            return None

def update_db(entry):
    """向数据库添加entry

    Args:
        entry   格式为dict

    """
    with sqlite3.connect(DATEBASE) as conn:
        cur = conn.cursor()
        l_entry = [entry[i] for i in query_column_names()]
        cur.execute('INSERT INTO updates VALUES (?,?,?,?,?,?,?,?,?,?)',l_entry)
        conn.commit()

def get_episodenums_by_series(series):
    """获得episodenums

    Args:
        series  type: string

    Returns:
        episode_nums    type: set
    """
    episode_nums = set()
    with sqlite3.connect(DATEBASE) as conn:
        cur = conn.cursor()
        cur.execute('SELECT title FROM updates WHERE series=?;',(series,))
        t = cur.fetchall()
        from parser.tackles import extract_episode
        for i in t:
            episode_nums.add(extract_episode(name))
    episode_nums.discard(None)
    return episode_nums

def has_entry(entry):
    """查询entry是否已经存在了

    Args:
        entry   type: dict

    Returns:
        True or False   type: bool
    """
    with sqlite3.connect(DATEBASE) as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM updates WHERE download_link=?;',(entry['download_link'],))
        t = cur.fetchone()
    if t:
        return True
    else:
        return False
