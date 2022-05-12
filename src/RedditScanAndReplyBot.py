import sqlite3
import praw # type: ignore
from util.sql_funcs import get_sql_cursor

class RedditScanAndReplyBot:
    def __init__(self):
        self._cursor = None
        self.PRAW = None

    @property
    def cur(self) -> sqlite3.Cursor:
        if self._cursor == None:
            raise Exception("No sql database connected. Cannot return cursor.")
        return self._cursor
    
    @cur.setter
    def cur(self, db_str):
        self._cursor = get_sql_cursor(db_str)