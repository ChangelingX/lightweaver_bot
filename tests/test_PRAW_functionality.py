import pytest
import sqlite3
from tests.conftest import MockSubmission
from util.praw_funcs import connect_to_reddit, get_submissions # type: ignore

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
            MockSubmission('t3_s1'),
            MockSubmission('t3_s2'),
            MockSubmission('t3_s3')
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
        