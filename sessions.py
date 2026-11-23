"""Yerel ders oturumları. SQLite işlemleri atomiktir; çalıştırılabilir nesne saklanmaz."""
from contextlib import contextmanager
import json
import os
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime

class SessionStore:
    def __init__(self, folder=None):
        folder = Path(folder or os.environ.get('WHISPER_STUDIO_DATA',
                     str(Path(os.environ.get('LOCALAPPDATA', Path.home()))/'WhisperStudio'/'sessions')))
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder/'dersler.sqlite3'
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS lessons(id TEXT PRIMARY KEY,title TEXT,updated TEXT,payload TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS preferences(key TEXT PRIMARY KEY,value TEXT)')
    @contextmanager
    def connect(self):
        connection=sqlite3.connect(self.path, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()
    def save(self, identity, title, payload):
        identity = identity or uuid.uuid4().hex
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO lessons VALUES(?,?,?,?)',
                       (identity,title,datetime.now().isoformat(timespec='seconds'),json.dumps(payload,ensure_ascii=False)))
            db.execute("INSERT OR REPLACE INTO preferences VALUES('last',?)",(identity,))
        return identity
    def list(self, query=''):
        with self.connect() as db:
            return db.execute('SELECT id,title,updated FROM lessons WHERE instr(lower(title),lower(?))>0 ORDER BY updated DESC',(query,)).fetchall()
    def load(self, identity):
        with self.connect() as db:
            row=db.execute('SELECT title,payload FROM lessons WHERE id=?',(identity,)).fetchone()
        return (row[0],json.loads(row[1])) if row else None
    def last(self):
        with self.connect() as db:
            row=db.execute("SELECT value FROM preferences WHERE key='last'").fetchone()
        return row[0] if row else None
