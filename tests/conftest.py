import re
import praw # type: ignore
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
        self.user = kwargs['username']
        self._subredditForest = MockSubredditForest()

    def setup_reddit(self):
        subreddit1 = MockSubreddit('mock_subreddit1')
        subreddit2 = MockSubreddit('mock_subreddit2')
        subreddit3 = MockSubreddit('mock_subreddit3')

        sr1_sub1 = MockSubmission('t3_s1')
        sr1_sub2 = MockSubmission('t3_s2')
        sr2_sub1 = MockSubmission('t3_s3')
        sr3_sub1 = MockSubmission('t3_s4')

        subreddit1.add_submission(sr1_sub1)
        subreddit1.add_submission(sr1_sub2)
        subreddit2.add_submission(sr2_sub1)
        subreddit3.add_submission(sr3_sub1)

        self._subredditForest.add_subreddit(subreddit1)
        self._subredditForest.add_subreddit(subreddit2)
        self._subredditForest.add_subreddit(subreddit3)

    def subreddit(self, subreddits=''):
        return self._subredditForest.subreddit(subreddits)

class MockSubredditForest:
    def __init__(self, subreddits=None, *args, **kwargs):
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
        
        return MockSubredditForest(returned_subs)

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

class MockSubreddit:
    def __init__(self, name, *args, **kwargs):
        self._submissions = []
        self.name = name

    def add_submission(self, submission):
        if not isinstance(submission, MockSubmission):
            raise Exception("Can't add a non-submission to MockSubreddit")

        self._submissions.append(submission)

    def new(self, limit=100):
        return self._submissions[:limit]

class MockSubmission:
    def __init__(self, fullname: str, *args, **kwargs):
        self._fullname = fullname

    def __eq__(self, other):
        return self.fullname == other.fullname
    
    def __repr__(self):
        return self.fullname

    @property
    def fullname(self) -> str:
        return self._fullname

class MockCommentForest:
    def __init__(self, comments=None, *args, **kwargs):
        if comments is None:
            self._comments = []
        else:
            self._comments = comments

    def add_comment(self, comment):
        self._comments.append(comment)
    
class MockComment:
    def __init__(self, fullname, body, *args, **kwargs):
        self._fullname = fullname
        self._body = body

    def __eq__(self, other):
        return self.fullname == other.fullname

    @property
    def fullname(self):
        return self._fullname

#### SQLITE MOCKS ####
@pytest.fixture
def amend_sqlite3_connect(mocker):
    original_func = sqlite3.connect

    def updated_func(db_name, *args, **kwargs):
        if db_name == './path' or (db_name == 'file:./path?mode=rw' and kwargs['uri'] == True):
            return original_func("file:./tests/test.db?mode=rw")

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