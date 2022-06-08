import argparse
import os
import sqlite3
import time
from configparser import ConfigParser, NoSectionError

import praw  # type: ignore
import schedule

from .util.praw_funcs import (connect_to_reddit, get_comments,  # type: ignore
                             get_submission, get_submissions,
                             get_thread_commenters, get_user_replied_entities,
                             post_comment, scan_entity)
from .util.sql_funcs import (add_replied_entry, create_database,  # type: ignore
                            get_book_db_entry, get_books, get_opted_in_users,
                            get_replied_entries, get_sql_cursor,
                            update_opted_in_users, update_replied_entry_table)


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
            if not {'client_id', 'client_secret', 'password', 'username', 'user_agent', 'opt_in_thread'}.issubset(praw_config):
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

    def initalize_database(self):
        """
        Performs first-time setup steps.
        Creates the database, confirms praw config is correct, ensures that opt-in thread exists.
        :raises sqlite3.* Exceptions: if the database cannot be created.
        :raises Exception: if the praw configuration does not return a valid praw.Reddit instance.
        :raises Exception: if the opt-in thread specified is not found.
        """
        try:
            create_database(self.configs['DATABASE']['database_name'])
        except (sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
            raise e 
        
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
        This is the main loop of this program.
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

        #for each post, add to the list of posts that have been replied to.
        for post in posted:
            add_replied_entry(self.cur, post.id, posted[post])

    def run(self):
        """
        Schedules and runs periodic tasks. This is the main loop.
        """
        schedule.every(1).minutes.do(self.scrape_reddit)
        schedule.every().hour.do(self.repopulate_opted_in_users)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def get_formatted_post_body(self, books_to_post: list) -> str:
        """
        Takes a list of books to be posted.
        Returns a Reddit Markdown formatted post body with book information and header/footer.
        
        :param books_to_post: list of books as string.
        :returns: Formatted string representing post body to be posted as a reply on Reddit.
        """
        header = f"Hello, I am {self.reddit.user.me()}. I am a bot that posts information on books that you have mentioned.\n\n------------------------\n"
        
        body = ""
        for book in books_to_post:
            book_info = get_book_db_entry(self.cur, book)
            book_info_formatted = '\n\n'.join([
                f"Title:  {book_info['title']}",
                f"Author: {book_info['author']}",
                f"ISBN:   {book_info['isbn']}",
                f"URI:    {book_info['uri']}"
            ])
            body = body + book_info_formatted + '\n\n------------------------\n\n' 

        footer = f"This post was made by a bot.\nFor more information, or to give feedback or suggestions, please visit /r/{self.configs['PRAW']['bot_subreddit']}."
        formatted_body = '\n'.join([header,body,footer])
        return formatted_body

    def repopulate_opted_in_users(self):
        """
        Connects to reddit, scrapes the opt-in thread for usersnames, then adds them to the opted_in_users table.
        :raises Exception: if praw is not connected to reddit.
        :raises Exception: if sql database is not connected.
        """
        submission = get_submission(self.reddit, URI=self.configs['PRAW']['opt_in_thread'])

        if submission is None:
            raise Exception(f"Submission {self.configs['PRAW']['opt_in_thread']} not found. Check config file.")
        
        opted_in_users = get_thread_commenters(submission)
        update_opted_in_users(self.cur, opted_in_users)

    def __repr__(self):
        as_string = f"Database Config: {self._database_config}\nReddit Config: {self._praw_config}"
        return as_string

    def repopulate_replied_entries(self):
        """
        Retrieves list of posts the bot has replied to on Reddit, updates replied_entries sql database to match.
        """
        entries_from_reddit = get_user_replied_entities(self.reddit)
        entries_to_add = {}
        for entry in entries_from_reddit:
            entries_to_add[entry] = True
        update_replied_entry_table(self.cur, entries_to_add)
    
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
        """
        Takes a dictionary of reddit configuration data. Check that required fields are present.
        Sets property if so, otherwise raises an exception.
        :param reddit_config: dict
        :raises Exception: if malformed dict is passed.
        """
        if not {'client_id','client_secret','password','username','user_agent','subreddits'}.issubset(reddit_config):
            raise Exception("Reddit config missing required fields. Check config data.")
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

def main(args):
    config = args.config
    initalize = args.initialize
    if config is None:
        raise Exception("No configuration file specified.")
    if not os.path.isfile(config):
        raise FileNotFoundError(f"Config file {config} not found.")
    if initalize:
        rb = RedditScanAndReplyBot().from_file(config)
        rb.initalize_database()
    else:
        rb = RedditScanAndReplyBot().from_file(config)
        rb.setup()
        rb.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scrapes reddit for hits on given keywords and posts relevant information as a reply.")
    parser.add_argument('--config', '-c', dest='config', required=True, metavar="./config_file.ini")
    parser.add_argument('--initialize', '-i', dest='initialize', required=False, action='store_true')
    args = parser.parse_args()
    main(args)
