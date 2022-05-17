import configparser
import re
import praw, prawcore # type: ignore
import pytest
import sqlite3
import os

### PRAW MOCKS ###
@pytest.fixture
def monkeysession(request):
    from _pytest.monkeypatch import MonkeyPatch

    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()

@pytest.fixture
def mock_reddit(monkeysession):
    monkeysession.setattr(praw, 'Reddit', MockReddit)

class MockReddit:
    def __init__(self, *args, **kwargs):
        self.user = MockRedditor(self, kwargs['username'])
        self._subredditForest = MockSubredditForest(self)

    def setup_reddit(self):
        subreddit1 = MockSubreddit(self, 'mock_subreddit1')
        subreddit2 = MockSubreddit(self, 'mock_subreddit2')
        subreddit3 = MockSubreddit(self, 'quarantined_subreddit', quarantined=True)

        sr1_sub1 = MockSubmission(self, subreddit1, 't3_s1', 'test_author1', 'title', 'selftext')
        sr1_sub2 = MockSubmission(self, subreddit1, 't3_s2', 'test_author1', 'title', 'selftext')
        sr2_sub1 = MockSubmission(self, subreddit2, 't3_s3', 'test_author1', 'Locked Submission', 'selftext', locked=True)
        sr3_sub1 = MockSubmission(self, subreddit3, 't3_s4', 'test_author1', 'title', 'selftext')

        sr1_sub1_c1 = MockComment(self, sr1_sub1, 't1_c1', 'test_author1', 'book1')
        sr1_sub1_c2 = MockComment(self, sr1_sub1, 't1_c2', 'test_author1', 'hello')
        sr2_sub1_c1 = MockComment(self, sr2_sub1, 't1_c3', 'test_author1', 'book1 locked_submission')
        sr3_sub1_c1 = MockComment(self, sr3_sub1, 't1_c4', 'test_author1', 'book1 quarantined subreddit')

        sr1_sub1.add_comment(sr1_sub1_c1)
        sr1_sub1.add_comment(sr1_sub1_c2)
        sr2_sub1.add_comment(sr2_sub1_c1)
        sr3_sub1.add_comment(sr3_sub1_c1)

        subreddit1.add_submission(sr1_sub1)
        subreddit1.add_submission(sr1_sub2)
        subreddit2.add_submission(sr2_sub1)
        subreddit3.add_submission(sr3_sub1)

        self._subredditForest.add_subreddit(subreddit1)
        self._subredditForest.add_subreddit(subreddit2)
        self._subredditForest.add_subreddit(subreddit3)

    def subreddit(self, subreddits=''):
        return self._subredditForest.subreddit(subreddits)

    def __eq__(self, other):
        if isinstance(other, MockReddit):
            return True

class MockSubredditForest:
    def __init__(self, reddit, subreddits=None, *args, **kwargs):
        self._reddit = reddit
        if subreddits is None:
            self._subreddits = []
        else:
            self._subreddits = subreddits
    
    def subreddit(self, subreddits=''):
        if subreddits == '':
            return self._subreddits
        returned_subs = []
        subs_to_return = re.split('\\W+', subreddits)
        for subreddit in self._subreddits:
            if subreddit.name in subs_to_return:
                returned_subs.append(subreddit)
        
        return MockSubredditForest(self.reddit, returned_subs)

    def add_subreddit(self, subreddit):
        if not isinstance(subreddit, MockSubreddit):
            raise Exception("Can't add a non-subreddit to MockSubredditForest")

        self._subreddits.append(subreddit)

    def new(self, limit=100):
        i = 0
        submissions_to_return = []
        for subreddit in self._subreddits:
            for submission in subreddit._submissions:
                submissions_to_return.append(submission)
                i += 1
                if i >= limit:
                    return submissions_to_return
        return submissions_to_return

    @property
    def reddit(self):
        return self._reddit

class MockSubreddit:
    def __init__(self, reddit, name, quarantined=False, *args, **kwargs):
        self._reddit = reddit
        self._submissions = []
        self.name = name
        self._quarantined = quarantined

    def add_submission(self, submission):
        if not isinstance(submission, MockSubmission):
            raise Exception("Can't add a non-submission to MockSubreddit")

        self._submissions.append(submission)

    def new(self, limit=100):
        return self._submissions[:limit]

    def __repr__(self):
        return self.name

    def __str__(self) -> str:
        return f"Subreddit: {self.name}\nQuarantined: {self.quarantined}"
        
    @property
    def quarantined(self) -> bool:
        return self._quarantined

    @property
    def reddit(self):
        return self._reddit

class MockSubmission:
    def __init__(self, reddit, parent, fullname: str, author, title, selftext, locked=False, *args, **kwargs):
        self._reddit = reddit
        self._parent = parent
        self._fullname = fullname
        self._author = author
        self._title = title
        self._selftext = selftext
        self._locked = locked
        self._comments = MockCommentForest(self.reddit, self)

    def __eq__(self, other):
        return self.fullname == other.fullname
    
    def __repr__(self):
        return self.fullname

    def __str__(self):
        return f"Fullname: {self.fullname}\nAuthor:{self.author}\nTitle:{self.title}\nSelftext:{self.selftext}\nLocked:{self.locked}"

    def add_comment(self, comment):
        self._comments.add_comment(comment)

    @property
    def comments(self):
        return self._comments

    @property
    def fullname(self) -> str:
        return self._fullname

    @property
    def author(self) -> str:
        return self._author

    @property
    def title(self) -> str:
        return self._title

    @property
    def selftext(self) -> str:
        return self._selftext

    @property
    def locked(self) -> bool:
        return self._locked

    @property
    def reddit(self):
        return self._reddit

    @property
    def parent(self):
        return self._parent

class MockCommentForest:
    def __init__(self, reddit, parent, comments=None, *args, **kwargs):
        self._reddit = reddit
        self._parent = parent
        if comments is None:
            self._comments = []
        else:
            self._comments = comments

    def add_comment(self, comment):
        self._comments.append(comment)

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        if self.n < len(self._comments):
            result = self._comments[self.n]
            self.n += 1
            return result
        else:
            raise StopIteration

    def new(self, limit=100):
        comments_to_return = []
        i = 0
        for comment in self._comments:
            if i < limit and i < len(self._comments):
                comments_to_return.append(comment)
                i += 1

        return comments_to_return

    @property
    def reddit(self):
        return self._reddit

    @property
    def parent(self):
        return self._parent

class MockComment:
    def __init__(self, reddit, parent, fullname, author, body, *args, **kwargs):
        self._reddit = reddit
        self._parent = parent
        self._fullname = fullname
        self._body = body
        self._author = author
        self._replies = MockCommentForest(self.reddit, self)

    def __eq__(self, other):
        return self.fullname == other.fullname

    def __repr__(self):
        return self.fullname

    def reply(self, reply_body):

        # recurse parent until we get to the submission.
        parent_type = self.parent.fullname.split("_")[0]
        top_level_parent = self.parent
        while parent_type != 't3':
            top_level_parent = self.parent.parent
            parent_type = parent_type = self.parent.fullname.split("_")[0]

        #parent is submission
        if  parent_type == 't3':
            #parent submission is locked.
            if top_level_parent.locked == True:
                class MockResponse():
                    def __init__(self, status_code):
                        self.status_code = status_code
                raise prawcore.exceptions.Forbidden(MockResponse(403))

        comment = MockComment(self.reddit, self, 't1_c5', self.reddit.user.me(), reply_body)
        self._replies.add_comment(comment)
        self.reddit.user.add_comment(comment)

        #Do not return comment if replying to quarantined subreddit.
        if top_level_parent.parent.quarantined == True:
            return None
        
        return comment

    @property
    def fullname(self):
        return self._fullname

    @property
    def author(self):
        return self._author

    @property
    def body(self):
        return self._body

    @property
    def reddit(self):
        return self._reddit

    @property
    def parent(self):
        return self._parent


class MockRedditor:
    def __init__(self, reddit, username):
        self._reddit = reddit
        self._username = username
        self._comments = MockCommentForest(reddit, self)

    def me(self):
        return self
    
    def __repr__(self):
        return self._username

    def add_comment(self, comment):
        self._comments.add_comment(comment)

    @property
    def comments(self):
        return self._comments
    
    @property
    def reddit(self):
        return self._reddit

#### SQLITE MOCKS ####
@pytest.fixture
def amend_sqlite3_connect(mocker):
    original_func = sqlite3.connect

    def updated_func(db_name, *args, **kwargs):
        if db_name == './path' or (db_name == 'file:./path?mode=rw' and kwargs['uri'] == True):
            return original_func("file:./tests/test.db?mode=rw", uri=True)

        return original_func(db_name, *args, **kwargs)
    
    mocker.patch('sqlite3.connect', new=updated_func)

@pytest.fixture
def setup_test_db():
    if os.path.exists("./tests/test.db"):
        os.remove("./tests/test.db")
    conn = sqlite3.connect("./tests/test.db")
    cur = conn.cursor()
    cur.execute('CREATE TABLE books(id integer PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, author text NOT NULL, isbn text NOT NULL, uri text, summary text not null)')
    cur.execute('CREATE TABLE replied_entries (id integer PRIMARY KEY AUTOINCREMENT, reddit_id TEXT NOT NULL)')
    cur.execute('CREATE TABLE opted_in_users (id integer PRIMARY KEY AUTOINCREMENT, reddit_username TEXT NOT NULL)')
    cur.execute('INSERT INTO books (title, author, isbn, uri, summary) VALUES (?,?,?,?,?)',('book1','author1','isbn1','url1','sum1'))
    cur.execute('INSERT INTO books (title, author, isbn, uri, summary) VALUES (?,?,?,?,?)',('book2','author2','isbn2','url2','sum2'))
    cur.execute('INSERT INTO books (title, author, isbn, uri, summary) VALUES (?,?,?,?,?)',('book3','author3','isbn3','url3','sum3'))
    cur.execute('INSERT INTO opted_in_users (reddit_username) VALUES (?)', ("test_author1",))
    cur.execute('INSERT INTO opted_in_users (reddit_username) VALUES (?)', ("test_author2",))
    cur.execute('INSERT INTO replied_entries (reddit_id) VALUES (?)',("t1_c1",))
    cur.execute('INSERT INTO replied_entries (reddit_id) VALUES (?)',("t3_s1",))
    cur.connection.commit()

#### CONFIGPARSER MOCKS ####
@pytest.fixture
def amend_configparser_read(mocker):
    original_func = configparser.ConfigParser.read

    def updated_func(self, filenames, *args, **kwargs):
        if filenames == './path':
            return original_func(self, './tests/example_config.ini')
        return original_func(self, filenames, *args, **kwargs)
    
    mocker.patch('configparser.ConfigParser.read', new=updated_func)

#### OS MOCKS ##
@pytest.fixture
def amend_os_path_isfile(mocker):
    original_func = os.path.isfile

    def updated_func(path, *args, **kwargs):
        if path == './path':
            return True
        
        return original_func(path, *args, **kwargs)
    
    mocker.patch('os.path.isfile', new=updated_func)