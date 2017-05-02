from modules.module import merge_args_yaml
from modules.global_var import DATEBASE
from main import parse_args_cli
import sqlite3

def delete_useless_db():
    args = parse_args_cli()
    config = merge_args_yaml(args)
    s_t_yml = [(i[4:],config['tasks'][i]['team']) for i in config['tasks']]
    with sqlite3.connect(DATEBASE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT series,team FROM updates")
        s_t_db = cur.fetchall()
        for i in s_t_db:
            if i not in s_t_yml:
                print(i)
                cur.execute("DELETE FROM updates WHERE series=? and team=?;",i)
        conn.commit()


if __name__ == '__main__':
    delete_useless_db()
