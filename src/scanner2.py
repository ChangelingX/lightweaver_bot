import praw #type: ignore
from praw.models import Submission #type: ignore
from praw.models import Comment #type: ignore
from praw.models import Subreddit #type: ignore
import sqlite3
from typing import Union
import typing

DATABASE='lightweaver.db'
BOT_PRAW_NAME = 'lightweaver'
SUBREDDITS = 'lightweaver_bot'

class RedditScanner:
    """
    This tool scrapes specific subreddits for mentions of specific books, 
    and responds to those posts with basic information on the books.
    """
    def __init__(self):
        #These are all external dependencies.
        self._reddit = None
        self._books = None
        self._opted_in_users = None

    def initalize_externals(self):
        """
        Configures the external dependencies for the bot.
        """
        self.connect_to_reddit()
        self.books = get_books()
        self.opted_in_users = get_opted_in_users()

    def get_submissions(self) -> typing.List[Submission]:
        """
        Iterates the submissions for assigned subreddits and returns a 
        list of submissions as Reddit.submission objects.

        :returns: list[Reddit.submission]
        """
        submissions = []
        for submission in self.subreddits.new():
            submissions.append(submission)
        return submissions
    
    def get_comments(self, submission: Union[Submission, Comment]) -> typing.List[Comment]:
        """
        Iterates the comments in a given submission and returns a 
        list of comments as Reddit.comment objects.
        
        :returns: A list of reddit comment objects as list(Reddit.comment).
        :raises ValueError: If invalid submission is passed.
        """
        comments = []
        comment_forest = submission.comments
        for comment in comment_forest:
            comments.append(comment)
        return comments

    #TODO: Scan_entity onwards

    @property
    def subreddits(self) -> Subreddit:
        """
        Retrieves subreddit object from praw.
        
        :returns: Subreddit model
        """
        subreddits = self.reddit.subreddit(SUBREDDITS)
        return subreddits   

    @property
    def reddit(self):
        return self._reddit

    def connect_to_reddit(self, bot_identifier=BOT_PRAW_NAME):
        reddit = praw.Reddit(bot_identifier)
        if not reddit.user.me():
            raise Exception("Failed to authenticate to Reddit.")
        self._reddit = reddit

    @property
    def books(self):
        return self._books

    @books.setter
    def books(self, books: typing.List[str]):
        self._books = books
    
    @property
    def opted_in_users(self):
        return self._opted_in_users

    @opted_in_users.setter
    def opted_in_users(self, users: typing.List[str]):
        self._opted_in_users = users

def get_books() -> typing.List[str]:
    """
    Connects to the sql database and returns the list of book titles to search for in reddit posts.

    :returns: List of book titles as list[str]
    """
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute('SELECT title FROM books')
    books = cur.fetchall()
    books = list({str(books).lower()})
    return books

def get_opted_in_users() -> typing.List[str]:
    """
    Connects to the sql database and returns a list of opted in users who wish to
    receive repies from this bot.
    
    :returns: list of usernames as list[str]
    """
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute('SELECT reddit_username FROM opted_in_users')
    temp_opted_in_users = cur.fetchall()
    opted_in_users = []
    for user in temp_opted_in_users:
        opted_in_users.append(user[0])
    return opted_in_users

def main():
    rs = RedditScanner()
    rs.initalize_externals()
    print(rs.reddit, rs.books, rs.opted_in_users)
    print(rs.subreddits)
    submissions = rs.get_submissions()
    print(submissions)
    comments = {}
    for submission in submissions:
        comments[submission] = rs.get_comments(submission)
        print(comments[submission])

if __name__ == '__main__':
    main()