from configparser import ConfigParser, NoSectionError
from logging import exception
import os
import sqlite3
import praw # type: ignore
from util.praw_funcs import connect_to_reddit, get_comments, get_submissions, post_comment, scan_entity # type: ignore
from util.sql_funcs import get_books, get_opted_in_users, get_replied_entries, get_sql_cursor # type: ignore

class RedditScanAndReplyBot:
    """
    This tool scrapes reddit for given keyword(s), and replies with a formatted text reply.
    """
    @classmethod
    def from_file(cls, init_file: str):
        """
        Reads in file from given location, parses out configurations and passes to init.
        
        :param init_file: str representation of file location.
        :raises FileNotFoundError: If init file does not exist.
        :raises Exception: If a section is not properly defined.
        """
        if not os.path.isfile(init_file):
            raise FileNotFoundError(f"Config file {init_file} not found.")
        
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

    def setup(self):
        """
        Connects to SQL database and Reddit using pre-set configuration data.
        :raises Exception: if database name not set or praw configuration not set.
        """
        if self.configs['DATABASE']['database_name'] is None:
            raise Exception("No database name specified. Cannot connect to database.")
        
        if self.configs['PRAW'] is None:
            raise Exception("No PRAW configuration specified. Cannot connect to Reddit.")
        
        self.cur = self.configs['DATABASE']['database_name']
        self.reddit = self.configs['PRAW']

    def  scrape_reddit(self):
        """
        Retrieves latest posts from tracked subreddits, scans them for keywords, and then posts the relevant replies.
        """
        submissions = get_submissions(self.reddit, self.configs['PRAW']['subreddits'])
        comments = {}
        books_to_post = {}
        books = get_books(self.cur)
        replied_entries = get_replied_entries(self.cur)
        opted_in_users = get_opted_in_users(self.cur)

        # scrape each submission title and selftext for hits, then scrape each reply within the submission.
        for submission in submissions:
            books_to_post[submission] = scan_entity(submission, books, replied_entries, opted_in_users)
            comments[submission] = get_comments(submission)
            for comment in comments[submission]:
                books_to_post[comment] = scan_entity(comment, books, replied_entries, opted_in_users)

        #For each hit, reply to the post with a formatted post body.
        posted = {}
        for reddit_post in books_to_post:
            if books_to_post[reddit_post] is None or len(books_to_post[reddit_post]) == 0:
                continue
            post_body = self.get_formatted_post_body(books_to_post[reddit_post])
            posted[reddit_post] = post_comment(self.reddit, reddit_post, post_body)

        #for each  post, add to the list of posts that have been replied to.
        for post in posted:
            print(f"Replying to:\n{post}\nReply succeeded:{posted[post]}\n---------------------")

    def get_formatted_post_body(self, books_to_post: list) -> str:
        """
        Takes a list of books to be posted.
        Returns a Reddit Markdown formatted post body with book information and header/footer.
        
        :param books_to_post: list of books as string.
        :returns: Formatted string representing post body to be posted as a reply on Reddit.
        """

        return str(books_to_post)

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
        if not {'client_id','client_secret','password','username','user_agent','subreddits'}.issubset(reddit_config):
            raise Exception("Reddit config missing required fields. Check config file.")
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
