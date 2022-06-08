import pytest
import prawcore # type: ignore
import sqlite3
from tests.conftest import MockComment, MockReddit, MockSubmission # type: ignore
from rsarb.util.praw_funcs import connect_to_reddit, get_submission, get_submissions, get_comments, get_thread_commenters, get_user_replied_entities, post_comment, scan_entity # type: ignore

class Test_PRAWFunctionality:
    def test_connect_to_reddit(self, mock_reddit):
        p = connect_to_reddit(
            'test_client_id',
            'test_client_secret',
            'test_password',
            'test_username',
            'test_user_agent'
        )
        assert str(p.user) == "test_username"

    def test_get_submissions(self, mock_reddit):
        p = connect_to_reddit(
            'test_client_id',
            'test_client_secret',
            'test_password',
            'test_username',
            'test_user_agent'
        )
        result = get_submissions(p, 'mock_subreddit1+mock_subreddit2')
        expected_result = [
            MockSubmission(p, None, 't3_s1', 'test_author1', 'title', 'selftext', None),
            MockSubmission(p, None, 't3_s2', 'test_author1', 'title', 'selftext', None),
            MockSubmission(p, None, 't3_s3', 'test_author1', 'title', 'selftext', None),
            MockSubmission(p, None, 't3_s4', 'test_author1', 'title', 'selftext', None)
        ]
        assert result == expected_result

    def test_get_submission_by_fullname(self, mock_reddit):
        p = connect_to_reddit(
            'test_client_id',
            'test_client_secret',
            'test_password',
            'test_username',
            'test_user_agent'
        )
        p.setup_reddit()
        result = get_submission(p, fullname='t3_s2')
        expected_result = MockSubmission(None, None, 't3_s2', None, None, None, None, None)
        assert result == expected_result

    def test_get_submission_by_URI(self, mock_reddit):
        p = connect_to_reddit(
            'test_client_id',
            'test_client_secret',
            'test_password',
            'test_username',
            'test_user_agent'
        )
        p.setup_reddit()
        result = get_submission(p, URI="https://www.mockreddit.com/r/mock_subreddit1/comments/1/title/")
        expected_result = MockSubmission(None, None, 't3_s1', None, None, None, None)
        assert result == expected_result

    def test_get_submission_not_found(self, mock_reddit):
        p = connect_to_reddit(
            'test_client_id',
            'test_client_secret',
            'test_password',
            'test_username',
            'test_user_agent'
        )
        p.setup_reddit()
        result = get_submission(p, URI="https://www.mockreddit.com/r/mock_subreddit1/1111111/title/")
        assert result is None

    def test_get_comments(self, mock_reddit):
        p = connect_to_reddit(
            'test_client_id',
            'test_client_secret',
            'test_password',
            'test_username',
            'test_user_agent'
        )
        p.setup_reddit()
        submission = p._subredditForest.subreddit()[0].new(limit=1)[0]
        result = get_comments(submission)
        expected_result = [
            MockComment(p, None, 't1_c1', 'test_author1', 'whatever'),
            MockComment(p, None, 't1_c2', 'test_author1', 'whatever'),
            MockComment(p, None, 't1_c3', 'test_author1', 'whatever')
        ]
        assert expected_result == result

    def test_scan_entity_comment_single_valid_match(self):
        entity = MockComment(None, None, 't1_c1', 'test_author1', 'book1')
        books = ['book1']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = scan_entity(entity, books, replied_entries, opted_in_users)
        expected_result = ['book1']
        assert result == expected_result

    def test_scan_entity_comment_multiple_valid_match(self):
        entity = MockComment(None, None, 't1_c1', 'test_author1', 'book1 book2')
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted(['book1', 'book2'])
        assert result == expected_result

    def test_scan_entity_comment_no_match(self):
        entity = MockComment(None, None, 't1_c1', 'test_author1', 'test')
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = scan_entity(entity, books, replied_entries, opted_in_users)
        expected_result = []
        assert result == expected_result

    def test_scan_entity_submission_single_match_in_title(self):
        entity = MockSubmission(None, None, 't3_s1', 'test_author1', 'book1', 'selftext', None)
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted(['book1'])
        assert result == expected_result

    def test_scan_entity_submission_multiple_match_in_title(self):
        entity = MockSubmission(None, None, 't3_s1', 'test_author1', 'book1 book2', 'selftext', None)
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted(['book1', 'book2'])
        assert result == expected_result

    def test_scan_entity_submission_single_match_in_selftext(self):
        entity = MockSubmission(None, None, 't3_s1', 'test_author1', 'title', 'book1', None)
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted(['book1'])
        assert result == expected_result

    def test_scan_entity_submission_multiple_match_in_selftext(self):
        entity = MockSubmission(None, None, 't3_s1', 'test_author1', 'title', 'book1 book2', None)
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted(['book1', 'book2'])
        assert result == expected_result

    def test_scan_entity_submission_single_match_in_title_and_selftext(self):
        entity = MockSubmission(None, None, 't3_s1', 'test_author1', 'book1', 'book2', None)
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted(['book1', 'book2'])
        assert result == expected_result

    def test_scan_entity_submission_multiple_match_in_title_and_selftext(self):
        entity = MockSubmission(None, None, 't3_s1', 'test_author1', 'book1 book2', 'book2', None)
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted(['book1', 'book2'])
        assert result == expected_result

    def test_scan_entity_submission_no_match(self):
        entity = MockSubmission(None, None, 't3_s1', 'test_author1', 'title', 'selftext', None)
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted([])
        assert result == expected_result
    
    def test_scan_entity_already_replied(self):
        entity = MockSubmission(None, None, 't3_s1', 'test_author1', 'book1 book2', 'book2', None)
        books = ['book1', 'book2']
        replied_entries = 't3_s1'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted([])
        assert result == expected_result

    def test_scan_entity_author_not_opted_in(self):
        entity = MockSubmission(None, None, 't3_s1', 'test_author2', 'title', 'selftext', None)
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted([])
        assert result == expected_result

    def test_post_comment_success(self, mock_reddit):
        p = connect_to_reddit(
            'test_client_id',
            'test_client_secret',
            'test_password',
            'test_username',
            'test_user_agent'
        )
        subreddit = p._subredditForest.subreddit("mock_subreddit1")._subreddits[0]
        submission = subreddit.new(limit=1)[0]
        comment = get_comments(submission)[0]
        result = post_comment(p, comment, "this is a comment")
        expected_result = True
        expected_post = MockComment(None, None, 't1_c11', None, None)
        assert result == expected_result
        assert expected_post in p.user.comments

    def test_post_comment_locked_post(self, mock_reddit):
        p = connect_to_reddit(
            'test_client_id',
            'test_client_secret',
            'test_password',
            'test_username',
            'test_user_agent'
        )
        subreddit = p._subredditForest.subreddit("mock_subreddit2")._subreddits[0]
        submission = subreddit.new(limit=1)[0]
        comment = get_comments(submission)[0]
        result = post_comment(p, comment, "this is a comment")
        expected_result = False
        assert result == expected_result
        
    def test_post_comment_quarantined_subreddit(self, mock_reddit):
        p = connect_to_reddit(
            'test_client_id',
            'test_client_secret',
            'test_password',
            'test_username',
            'test_user_agent'
        )
        subreddit = p._subredditForest.subreddit("quarantined_subreddit")._subreddits[0]
        submission = subreddit.new(limit=1)[0]
        comment = get_comments(submission)[0]
        result = post_comment(p, comment, "this is a comment")
        expected_comment = MockComment(None, None, 't1_c11', None, None)
        expected_result = True
        assert result is expected_result
        assert expected_comment in p.user.comments

    def test_get_thread_commenters_simple(self, mock_reddit):
        p = connect_to_reddit(
            'test_client_id',
            'test_client_secret',
            'test_password',
            'test_username',
            'test_user_agent'
        )
        p.setup_reddit()
        submission = get_submission(p, fullname="t3_s4")
        commenters = sorted(get_thread_commenters(submission))
        expected_result = sorted(['test_author1', 'test_author2'])
        assert commenters == expected_result

    def test_get_thread_commenters_duplicate_authors(self, mock_reddit):
        p = connect_to_reddit(
            'test_client_id',
            'test_client_secret',
            'test_password',
            'test_username',
            'test_user_agent'
        )
        p.setup_reddit()
        submission = get_submission(p, URI="https://www.mockreddit.com/r/mock_subreddit1/comments/1/title/")
        commenters = get_thread_commenters(submission)
        expected_result = ['test_author1']
        assert commenters == expected_result

    def test_get_thread_commenters_no_posts(self, mock_reddit):
        p = connect_to_reddit(
            'test_client_id',
            'test_client_secret',
            'test_password',
            'test_username',
            'test_user_agent'
        )
        p.setup_reddit()
        submission = get_submission(p, fullname="t3_s2")
        commenters = sorted(get_thread_commenters(submission))
        expected_result = []
        assert commenters == expected_result

    def test_get_user_replies(self, mock_reddit):
        p = connect_to_reddit(
            'test_client_id',
            'test_client_secret',
            'test_password',
            'test_username',
            'test_user_agent'
        )
        p.setup_reddit()
        submission = p.get_submissions()[0]
        submission.reply("test1")
        submission.reply("test2")
        submission.reply("test3")
        submission = p.get_submissions()[1]
        submission.reply("test4")
        results = sorted(get_user_replied_entities(p))
        expected_results = ['s1', 's2']
        assert results == expected_results
