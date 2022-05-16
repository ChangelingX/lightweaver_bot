from configparser import ConfigParser, NoSectionError
from logging import exception
import os
import sqlite3
import praw
from util.praw_funcs import connect_to_reddit # type: ignore
from util.sql_funcs import get_sql_cursor # type: ignore

class RedditScanAndReplyBot:
    """
    This tool scrapes reddit for given keyword(s), and replies with a formatted text reply.
    """
    @classmethod
    def from_file(cls, init_file: str):
        if not os.path.isfile(init_file):
            raise ValueError(f"Config file {init_file} not found.")
        
        parser = ConfigParser()
        parser.read(init_file)
        try:
            
            praw_config = {k:v for k, v in parser.items('PRAW')}
            if not {'client_id', 'client_secret', 'password', 'username', 'user_agent'}.issubset(praw_config):
                raise Exception(f"{init_file} section [PRAW] does not contain required key=value pairs.")

            database_config = {k:v for k, v in parser.items('DATABASE')}
            if 'database_name' not in database_config:
                raise Exception(f"{init_file} section [DATABASE] does not contain required key=value pairs.")

        except NoSectionError as err:
            raise Exception(f"{init_file} does not contain the valid sections.")
        
        return cls(praw_config, database_config)
    
    def __init__(self, praw_config=None, database_config=None):
        self._praw_config = praw_config
        self._database_config = database_config
        self._cursor = None
        self._reddit = None

    def __repr__(self):
        as_string = f"Database Config: {self._database_config}\nReddit Config: {self._praw_config}"
        return as_string
    
    @property
    def configs(self) -> dict:
        configs = {}
        configs['DATABASE'] = self._database_config
        configs['PRAW'] = self._praw_config
        return configs

    @property
    def reddit(self) -> praw.Reddit:
        if self._reddit == None:
            raise Exception("Not connected to reddit.")
        return self._reddit

    @reddit.setter
    def reddit(self, reddit_config: dict):
        self._reddit = connect_to_reddit(
            reddit_config['client_id'], 
            reddit_config['client_secret'], 
            reddit_config['password'], 
            reddit_config['username'], 
            reddit_config['user_agent'], 
            )

    @property
    def cur(self) -> sqlite3.Cursor:
        if self._cursor == None:
            raise Exception("No sql database connected. Cannot return cursor.")
        return self._cursor
    
    @cur.setter
    def cur(self, db_file: str):
        self._cursor = get_sql_cursor(db_file)
