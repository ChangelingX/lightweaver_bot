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
        self._replied_entries = None

    def initalize_externals(self):
        """
        Configures the external dependencies for the bot.
        """
        self.connect_to_reddit()
        self.books = get_books()
        self.opted_in_users = get_opted_in_users()
        self.replied_entries = get_replied_entries()

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

    def scan_entity(self, entity: Union[Submission, Comment]) -> Union[None, typing.List[Comment],typing.List[Submission]]:
        """
        Scans a given entity (submission, comment) and detects book titles by name
        scans the title of submissions, and the body of submissions and comments
        returns a list of books to reply to a given entity with.

        :param entity: A reddit comment or submission.
        :returns: list[book1, book2, book3, ...]
        :raises ValueError: If entity is not a valid comment or submission.
        """
        type_string, reddit_id = entity.fullname.split('_')
        if type_string not in ['t1','t3']:
            raise ValueError("Entity submitted is not a valid submission or comment.")

        if reddit_id in self.replied_entries:
            return None
        
        if entity.author == self.reddit.user.me():
            return None

        if entity.author not in self.opted_in_users:
            return None

        found_books = []
        for book in self.books:

             #submission
            if type_string == 't3':
                if book in entity.title.lower() or book in entity.selftext.lower():
                    found_books.append(book)

            #comment
            if type_string == 't1':
                if book in entity.body.lower():
                    found_books.append(book)

        found_books = list({str(book).lower() for book in found_books}) #de-duplicate list.

        return found_books

    def post_comment(self, entity: Union[Submission, Comment], books: list) -> None:
        """
        Accepts an entity to reply to and a list of books to post information for.
        Posts the book information in a formatted block as a reply to the provided entity.

        :param entity: the Reddit object to reply to (submission or comment)
        :param books: a list of books as list[str]
        :returns: None
        :raises: Exception when post does not submit to reddit properly.

        """
        post_body = get_formatted_post_body(books)

        posted_reply = entity.reply(post_body)

        if posted_reply is None:
            raise Exception("Unknown error has occured while attempting to post reply to {entity.fullname}.")
        
        update_replied_entries_table(entity)

    def get_subreddits(self, subreddits_to_scan=SUBREDDITS) -> Subreddit:
        """
        Retrieves subreddit object from praw.
        
        :returns: Subreddit model
        """
        subreddits = self.reddit.subreddit(subreddits_to_scan)
        return subreddits

    @property
    def subreddits(self) -> Subreddit:
        return self.get_subreddits()

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

    @property
    def replied_entres(self):
        return self._replied_entries

    def __str__(self) -> str:
        str_to_return = "-----------------------------------\n"+\
                        f"Reddit: {self.reddit}\n"+\
                        f"Books: {self.books}\n"+\
                        f"Users: {self.opted_in_users}\n"+\
                        f"Entries: {self.replied_entries}\n"+\
                        "-----------------------------------"
        return str_to_return


#Below are all the SQLlite3 Database interaction functions.
def get_books() -> typing.List[str]:
    """
    Connects to the sql database and returns the list of book titles to search for in reddit posts.

    :returns: List of book titles as list[str]
    """
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute('SELECT title FROM books')
    books = cur.fetchall()
    books = list({str(book[0]).lower() for book in books})
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

def get_replied_entries() -> typing.List[str]:
    con = sqlite3.connect(DATABASE) #check if we have already replied to a given entity
    cur = con.cursor()
    cur.execute("SELECT reddit_id FROM replied_entries")
    already_replied = cur.fetchall()
    already_replied = list({str(entry[0]) for entry in already_replied})
    return already_replied

def get_formatted_post_body(books: typing.List[str]) -> str:
    """
    Accepts a list of books by title, formats them into a complete post body for a text post.
    
    :param books: list[str]
    :returns: str
    """
    post_body = ""
    header = "Hello, I am Lightweaver_bot. I post information on books mentioned in the parent comment or submission.\n\n"

    for book in books:
        post_body = post_body + "--------------------------------\n\n" + get_book_db_entry(book)

    footer = "--------------------------------\n\n"+\
             "Please DM this bot, the author, or post on /r/lightweaver_bot with any feedback or suggestions.\n"+\
             "Author: /u/HoweveritHasToHappen\n\n"

    post_body = header + post_body + footer
    return post_body

def get_book_db_entry(title: str) -> str:
    """
    Accepts a title of a book. Returns the database entry for that book in a formatted block.
    
    :param title: str
    :returns: str
    :raises KeyError: If title is not found in database.
    """
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute("SELECT * FROM books WHERE title = ? COLLATE NOCASE", [title])
    book_db_entry = cur.fetchone()

    if book_db_entry is None:
        raise KeyError("Title not found in database.")

    book_db_entry = "Title:\t"+book_db_entry[1]+"\n\n"+\
                    "Author:\t"+book_db_entry[2]+"\n\n"+\
                    "ISBN:\t"+book_db_entry[3]+"\n\n"+\
                    "URI:\t"+book_db_entry[4]+"\n\n"#+\
                    #"Desc:\t"+book_db_entry[5]+"\n\n"
    return book_db_entry

def update_replied_entries_table(entity: Union[Submission, Comment], database=DATABASE) -> None:
    con = sqlite3.connect(database)
    cur = con.cursor()
    cur.execute("INSERT INTO replied_entries (reddit_id) VALUES (?)", [entity.id])
    con.commit()

def main():
    rs = RedditScanner()
    rs.initalize_externals()
    print(rs)
    print(f"Subreddits: {rs.subreddits}")
    submissions = rs.get_submissions()
    print("Submissions: ", submissions)
    comments = {}
    for submission in submissions:
        comments[submission] = rs.get_comments(submission)
        #print(f"Submission: {submission.title}\nComments: {comments[submission]}")
    
    books_to_post = {}

    for submission in submissions:
        books_to_post[submission] = rs.scan_entity(submission)
        #print(f"Submission scanned: {submission.title}\n Comments to reply to: {books_to_post[submission]}")
        for comment in comments[submission]:
            books_to_post[comment] = rs.scan_entity(comment)
    
    for reddit_post in books_to_post:
        if books_to_post[reddit_post] is None or len(books_to_post[reddit_post]) == 0:
            continue
        #print(f"Entity: {reddit_post} - Hits: {books_to_post[reddit_post]}")
        rs.post_comment(reddit_post, books_to_post[reddit_post])

if __name__ == '__main__':
    main()