import praw
import pytest

@pytest.fixture(scope="session")
def monkeysession(request):
    from _pytest.monkeypatch import MonkeyPatch

    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()

# noinspection PyMethodMayBeStatic
class MockRedditor:
    def me(self):
        return 'Mocked_Redditor'

class MockComment:
    def __init__(self, body):
        self.body = body

class MockSubmission:
    def __init__(self, title, selftext, comments):
        self.title = title
        self.author = 'testauthor'
        self.selftext = selftext
        self.comments = comments

# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class MockSubreddit:
    def __init__(self, display_name:str, *args, **kwargs):
        self.display_name = display_name

    def __repr__(self):
        return self.display_name

    def controversial(self, *args, **kwargs):
        return [MockSubmission('controversial') for _ in range(kwargs['limit'])]

    def gilded(self, *args, **kwargs):
        return [MockSubmission('gilded') for _ in range(kwargs['limit'])]

    def hot(self, *args, **kwargs):
        return [MockSubmission('hot') for _ in range(kwargs['limit'])]

    def new(self, *args, **kwargs):
        comment1 = MockComment("hello")
        comment2 = MockComment('goodbye')
        comment3 = MockComment('Opening the Hand of Thought')
        comments1 = [comment1, comment2, comment3]
        submission1 = MockSubmission('Opening the Hand of Thought', 'test', comments1)
        submission2 = MockSubmission('nohit','test',comments1)
        contents = [submission1, submission2]
        return contents

    def random_rising(self, *args, **kwargs):
        return [MockSubmission('random_rising') for _ in range(kwargs['limit'])]

    def rising(self, *args, **kwargs):
        return [MockSubmission('rising') for _ in range(kwargs['limit'])]

    def top(self, *args, **kwargs):
        return [MockSubmission('top') for _ in range(kwargs['limit'])]

# noinspection PyUnusedLocal
class MockReddit:
    def __init__(self, *args, **kwargs):
        self.user = MockRedditor()
        self.subreddit = MockSubreddit

@pytest.fixture(scope='session', autouse=True)
def mock_reddit(monkeysession):
    monkeysession.setattr(praw, 'Reddit', MockReddit)