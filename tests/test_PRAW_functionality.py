import pytest
import sqlite3
from tests.conftest import MockComment, MockSubmission
from util.praw_funcs import connect_to_reddit, get_submissions, get_comments, scan_entity # type: ignore

class Test_PRAWFunctionality:
    def test_connect_to_reddit(self, mock_reddit):
        p = connect_to_reddit(
            'test_client_id',
            'test_client_secret',
            'test_password',
            'test_username',
            'test_user_agent'
        )
        #TODO revisit this test once mocks are finished.

    def test_get_submissions(self, mock_reddit):
        p = connect_to_reddit(
            'test_client_id',
            'test_client_secret',
            'test_password',
            'test_username',
            'test_user_agent'
        )
        p.setup_reddit()
        result = get_submissions(p, 'mock_subreddit1+mock_subreddit2')
        expected_result = [
            MockSubmission('t3_s1', 'test_author1', 'title', 'selftext'),
            MockSubmission('t3_s2', 'test_author1', 'title', 'selftext'),
            MockSubmission('t3_s3', 'test_author1', 'title', 'selftext')
        ]
        assert result == expected_result

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
            MockComment('t1_c1', 'test_author1', 'whatever'),
            MockComment('t1_c2', 'test_author1', 'whatever')
        ]
        assert expected_result == result

    def test_scan_entity_comment_single_valid_match(self):
        entity = MockComment('t1_c1', 'test_author1', 'book1')
        books = ['book1']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = scan_entity(entity, books, replied_entries, opted_in_users)
        expected_result = ['book1']
        assert result == expected_result

    def test_scan_entity_comment_multiple_valid_match(self):
        entity = MockComment('t1_c1', 'test_author1', 'book1 book2')
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted(['book1', 'book2'])
        assert result == expected_result

    def test_scan_entity_comment_no_match(self):
        entity = MockComment('t1_c1', 'test_author1', 'test')
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = scan_entity(entity, books, replied_entries, opted_in_users)
        expected_result = []
        assert result == expected_result

    def test_scan_entity_submission_single_match_in_title(self):
        entity = MockSubmission('t3_s1', 'test_author1', 'book1', 'selftext')
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted(['book1'])
        assert result == expected_result

    def test_scan_entity_submission_multiple_match_in_title(self):
        entity = MockSubmission('t3_s1', 'test_author1', 'book1 book2', 'selftext')
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted(['book1', 'book2'])
        assert result == expected_result

    def test_scan_entity_submission_single_match_in_selftext(self):
        entity = MockSubmission('t3_s1', 'test_author1', 'title', 'book1')
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted(['book1'])
        assert result == expected_result

    def test_scan_entity_submission_multiple_match_in_selftext(self):
        entity = MockSubmission('t3_s1', 'test_author1', 'title', 'book1 book2')
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted(['book1', 'book2'])
        assert result == expected_result

    def test_scan_entity_submission_single_match_in_title_and_selftext(self):
        entity = MockSubmission('t3_s1', 'test_author1', 'book1', 'book2')
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted(['book1', 'book2'])
        assert result == expected_result

    def test_scan_entity_submission_multiple_match_in_title_and_selftext(self):
        entity = MockSubmission('t3_s1', 'test_author1', 'book1 book2', 'book2')
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted(['book1', 'book2'])
        assert result == expected_result

    def test_scan_entity_submission_no_match(self):
        entity = MockSubmission('t3_s1', 'test_author1', 'title', 'selftext')
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted([])
        assert result == expected_result
    
    def test_scan_entity_already_replied(self):
        entity = MockSubmission('t3_s1', 'test_author1', 'book1 book2', 'book2')
        books = ['book1', 'book2']
        replied_entries = 't3_s1'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted([])
        assert result == expected_result

    def test_scan_entity_author_not_opted_in(self):
        entity = MockSubmission('t3_s1', 'test_author2', 'title', 'selftext')
        books = ['book1', 'book2']
        replied_entries = 't1_c2'
        opted_in_users = 'test_author1'
        result = sorted(scan_entity(entity, books, replied_entries, opted_in_users))
        expected_result = sorted([])
        assert result == expected_result

    def test_post_comment_success(self, mock_reddit):
        pass

    def test_post_comment_locked_post(self, mock_reddit):
        p = connect_to_reddit(
            'test_client_id',
            'test_client_secret',
            'test_password',
            'test_username',
            'test_user_agent'
        )
        p.setup_reddit()
        subreddit = p._subredditForest.subreddit("mock_subreddit2")._subreddits[0]
        submission = subreddit.new(limit=1)[0]
        print(f"\n------------\n{subreddit.__str__()}\n------------")
        print(f"{submission.__str__()}\n")
        result = get_comments(submission)
        print(result)

    def test_post_comment_quarantined_subreddit(self, mock_reddit):
        p = connect_to_reddit(
            'test_client_id',
            'test_client_secret',
            'test_password',
            'test_username',
            'test_user_agent'
        )
        p.setup_reddit()
        subreddit = p._subredditForest.subreddit("quarantined_subreddit")._subreddits[0]
        submission = subreddit.new(limit=1)[0]
        print(f"\n------------\n{subreddit.__str__()}\n------------")
        print(f"{submission.__str__()}\n")
        result = get_comments(submission)
        print(result)

