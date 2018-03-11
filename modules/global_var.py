import os

WORKPATH = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
DATEBASE = os.path.join(WORKPATH,'bangumi.db')
TASKS = os.path.join(WORKPATH,'tasks.sh')
