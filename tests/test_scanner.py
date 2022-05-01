import pytest

from scanner import RedditScanner

class Test_RedditScanner:
    def test_retrieves_submissions(self, mock_reddit):
        rs = RedditScanner()
        submissions = rs.get_submissions()
        print(submissions)
        