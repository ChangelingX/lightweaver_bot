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
        self.tld = 'https://www.mockreddit.com'
        self._subredditForest = MockSubredditForest(self)
        self._next_comment_id = 't1_c1'
        self._next_submission_id = 't3_s1'
        self._next_permalink_id = 1

    def setup_reddit(self):
        subreddit1 = MockSubreddit(self, 'mock_subreddit1')
        subreddit2 = MockSubreddit(self, 'mock_subreddit2')
        subreddit3 = MockSubreddit(self, 'quarantined_subreddit', quarantined=True)
        subreddit4 = MockSubreddit(self, 'mock_botsubreddit')

        sr1_sub1 = MockSubmission(self, subreddit1, self.next_submission_id, 'test_author1', 'title', 'selftext', self.next_permalink_id)
        sr1_sub2 = MockSubmission(self, subreddit1, self.next_submission_id, 'test_author1', 'title', 'selftext', self.next_permalink_id)
        sr1_sub3 = MockSubmission(self, subreddit1, self.next_submission_id, 'test_author1', 'book1', 'selftext', self.next_permalink_id)
        sr2_sub1 = MockSubmission(self, subreddit2, self.next_submission_id, 'test_author1', 'locked_submission', 'selftext', self.next_permalink_id, locked=True)
        sr3_sub1 = MockSubmission(self, subreddit3, self.next_submission_id, 'test_author1', 'title', 'selftext', self.next_permalink_id)
        sr4_sub1 = MockSubmission(self, subreddit4, self.next_submission_id, 'test_author1', 'opt_in_thread', 'post here to opt in', self.next_permalink_id)

        sr1_sub1_c1 = MockComment(self, sr1_sub1, self.next_comment_id, 'test_author1', 'book1')
        sr1_sub1_c2 = MockComment(self, sr1_sub1, self.next_comment_id, 'test_author1', 'hello')
        sr1_sub1_c3 = MockComment(self, sr1_sub1, self.next_comment_id, 'test_author1', 'book1')
        sr2_sub1_c1 = MockComment(self, sr2_sub1, self.next_comment_id, 'test_author1', 'book1 locked_submission')
        sr2_sub1_c2 = MockComment(self, sr2_sub1, self.next_comment_id, 'test_author2', 'book1 locked_submission')
        sr3_sub1_c1 = MockComment(self, sr3_sub1, self.next_comment_id, 'test_author1', 'book1 quarantined subreddit')
        sr4_sub1_c1 = MockComment(self, sr3_sub1, self.next_comment_id, 'test_author1', 'subscribe me!')
        sr4_sub1_c2 = MockComment(self, sr3_sub1, self.next_comment_id, 'test_author2', 'subscribe me!')
        sr4_sub1_c3 = MockComment(self, sr3_sub1, self.next_comment_id, 'test_author3', 'subscribe me!')
        sr4_sub1_c4 = MockComment(self, sr3_sub1, self.next_comment_id, 'test_author4', 'subscribe me!')

        sr1_sub1.add_comment(sr1_sub1_c1)
        sr1_sub1.add_comment(sr1_sub1_c2)
        sr1_sub1.add_comment(sr1_sub1_c3)
        sr2_sub1.add_comment(sr2_sub1_c1)
        sr2_sub1.add_comment(sr2_sub1_c2)
        sr3_sub1.add_comment(sr3_sub1_c1)
        sr4_sub1.add_comment(sr4_sub1_c1)
        sr4_sub1.add_comment(sr4_sub1_c2)
        sr4_sub1.add_comment(sr4_sub1_c3)
        sr4_sub1.add_comment(sr4_sub1_c4)

        subreddit1.add_submission(sr1_sub1)
        subreddit1.add_submission(sr1_sub2)
        subreddit1.add_submission(sr1_sub3)
        subreddit2.add_submission(sr2_sub1)
        subreddit3.add_submission(sr3_sub1)
        subreddit4.add_submission(sr4_sub1)

        self._subredditForest.add_subreddit(subreddit1)
        self._subredditForest.add_subreddit(subreddit2)
        self._subredditForest.add_subreddit(subreddit3)
        self._subredditForest.add_subreddit(subreddit4)

    def subreddit(self, subreddits=''):
        return self._subredditForest.subreddit(subreddits)

    def submission(self, name=None, permalink=None):
        return self._subredditForest.submission(name=name, permalink=permalink)

    def get_submissions(self):
        return self._subredditForest.get_submissions()
        
    def __eq__(self, other):
        if isinstance(other, MockReddit):
            return True

    @property
    def next_comment_id(self):
        current_comment_id = self._next_comment_id
        next_comment_id_int = int(current_comment_id[4:])+1
        self._next_comment_id = "t1_c"+str(next_comment_id_int)
        return current_comment_id

    @property
    def next_submission_id(self):
        current_submission_id = self._next_submission_id
        next_submission_id_int = int(current_submission_id[4:])+1
        self._next_submission_id = "t3_s"+str(next_submission_id_int)
        return current_submission_id

    @property
    def next_permalink_id(self):
        current_permalink_id = self._next_permalink_id
        self._next_permalink_id = current_permalink_id + 1
        return current_permalink_id

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
    
    def submission(self, permalink=None, name=None):
        for subreddit in self._subreddits:
            if subreddit.submission(permalink=permalink, name=name) is not None:
                return subreddit.submission(permalink=permalink, name=name)

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

    def get_submissions(self):
        submissions = []
        for subreddit in self._subreddits:
            for submission in subreddit._submissions:
                submissions.append(submission)
        return submissions

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

    def submission(self, name=None, permalink=None):
        for submission in self._submissions:
            if submission.name == name:
                return submission
            if submission.permalink == permalink:
                return submission

    def new(self, limit=100):
        return self._submissions[:limit]

    def __repr__(self):
        return self.name

    def __str__(self) -> str:
        as_string = "-------SUBREDDIT-------\n"+\
                    f"Subreddit: {self.name}\n"+\
                    f"Quarantined: {self.quarantined}"
        return as_string
        
    @property
    def quarantined(self) -> bool:
        return self._quarantined

    @property
    def reddit(self):
        return self._reddit

class MockSubmission:
    def __init__(self, reddit, parent, fullname: str, author, title: str, selftext: str, shortlink, locked=False, *args, **kwargs):
        self._reddit = reddit
        self._parent = parent
        self._fullname = fullname
        self._author = author
        self._title = title
        self._selftext = selftext
        self._shortlink = shortlink
        self._locked = locked
        self._comments = MockCommentForest(self.reddit, self)

    def reply(self, reply_body):

        # recurse parent until we get to the submission.
        parent_type = self.fullname.split("_")[0]
        top_level_parent = self
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

        comment = MockComment(self.reddit, self, self.reddit.next_comment_id, self.reddit.user.me(), reply_body)
        self._comments.add_comment(comment)
        self.reddit.user.add_comment(comment)

        #Do not return comment if replying to quarantined subreddit.
        if top_level_parent.parent.quarantined == True:
            return None
        
        return comment

    def __eq__(self, other):
        return self.fullname == other.fullname
    
    def __repr__(self):
        return self.fullname

    def __hash__(self):
        return hash(repr(self))

    def __str__(self):
        return f"Fullname: {self.fullname}\nAuthor:{self.author}\nTitle:{self.title}\nSelftext:{self.selftext}\nLink:{self.permalink}\nLocked:{self.locked}"

    def add_comment(self, comment):
        self._comments.add_comment(comment)

    @property
    def comments(self):
        return self._comments

    @property
    def fullname(self) -> str:
        return self._fullname

    @property
    def name(self) -> str:
        return self._fullname.split("_")[1]

    @property
    def permalink(self) -> str:
        link = f"{self.reddit.tld}/r/{self.parent.name}/comments/{self._shortlink}/{self.title}/"
        return link

    @property
    def shortlink(self) -> str:
        link = f"https://redd.it/{self._shortlink}"
        return link

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
        for comment in sorted(self._comments, reverse=True):
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

    def __lt__(self, other):
        if self.fullname < other.fullname:
            return True
        return False

    def __repr__(self):
        return self.fullname

    def __str__(self):
        as_string = "-------COMMENT-------\n"+\
                    f"Parent: {repr(self.parent)}\n"+\
                    f"Fullname: {self.fullname}\n"+\
                    f"Author: {self.author}\n"+\
                    f"Body: {self.body}\n"
        return as_string

    def __hash__(self):
        return hash(repr(self))

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

        comment = MockComment(self.reddit, self, self.reddit.next_comment_id, self.reddit.user.me(), reply_body)
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

    @property
    def parent_id(self):
        return self.parent.fullname


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
        if db_name == './wrong_schema' or (db_name == 'file:./wrong_schema?mode=rw' and kwargs['uri'] == True):
            return original_func("file:./tests/wrong_schema.db?mode=rw", uri=True)
        if db_name == './not-a-db':
            return original_func("file:./tests/not-a-db?mode=rw", uri=True)
        return original_func(db_name, *args, **kwargs)
    
    mocker.patch('sqlite3.connect', new=updated_func)

@pytest.fixture
def setup_test_db():
    if os.path.exists("./tests/test.db"):
        os.remove("./tests/test.db")
    conn = sqlite3.connect("./tests/test.db")
    cur = conn.cursor()
    cur.execute('CREATE TABLE books(id integer PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, author text NOT NULL, isbn text NOT NULL, uri text, summary text not null)')
    cur.execute('CREATE TABLE replied_entries (id integer PRIMARY KEY AUTOINCREMENT, reddit_id TEXT NOT NULL, reply_succeeded_bool integer NOT NULL)')
    cur.execute('CREATE TABLE opted_in_users (id integer PRIMARY KEY AUTOINCREMENT, reddit_username TEXT UNIQUE NOT NULL)')
    cur.execute('INSERT INTO books (title, author, isbn, uri, summary) VALUES (?,?,?,?,?)',('book1','author1','isbn1','url1','sum1'))
    cur.execute('INSERT INTO books (title, author, isbn, uri, summary) VALUES (?,?,?,?,?)',('book2','author2','isbn2','url2','sum2'))
    cur.execute('INSERT INTO books (title, author, isbn, uri, summary) VALUES (?,?,?,?,?)',('book3','author3','isbn3','url3','sum3'))
    cur.execute('INSERT INTO opted_in_users (reddit_username) VALUES (?)', ("test_author1",))
    cur.execute('INSERT INTO opted_in_users (reddit_username) VALUES (?)', ("test_author2",))
    cur.execute('INSERT INTO replied_entries (reddit_id, reply_succeeded_bool) VALUES (?, ?)',("c1","1",))
    cur.execute('INSERT INTO replied_entries (reddit_id, reply_succeeded_bool) VALUES (?, ?)',("s1","1",))
    cur.connection.commit()

    if os.path.exists("./tests/wrong_schema.db"):
        os.remove("./tests/wrong_schema.db")
    conn = sqlite3.connect("./tests/wrong_schema.db")
    cur = conn.cursor()
    cur.execute('CREATE TABLE books(id integer PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, author text NOT NULL, isbn text NOT NULL, uri text, summary text not null)')
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