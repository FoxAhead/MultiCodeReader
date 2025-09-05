import os
import sqlite3
from flask import g

DATABASE = 'database.db'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def close_connection(exception):
    """Закрывает соединение с с БД"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def init_db(app):
    if not os.path.exists('database.db'):
        with app.app_context():
            db = get_db()
            with app.open_resource('database.db.sql', mode='r') as f:
                db.cursor().executescript(f.read())
            db.commit()


def get_app_param_value(param):
    value = query_db('SELECT value FROM app WHERE param = ?', [param], one=True)
    return value


def get_current_box_id():
    box_id = get_app_param_value("current_box_id")
    return box_id
