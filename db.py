import pymysql
from pymysql.cursors import DictCursor
from flask import g
from config import Config

def get_db():
    if 'db' not in g:
        g.db = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            cursorclass=DictCursor,
            autocommit=True
        )
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
