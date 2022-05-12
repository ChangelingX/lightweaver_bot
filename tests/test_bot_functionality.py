import pytest
import sqlite3 
from RedditScanAndReplyBot import RedditScanAndReplyBot

class Test_BotFunctionality:
    
    @pytest.mark.usefixtures('setup_test_db')
    def test_connect(self, amend_sqlite3_connect):
        rb = RedditScanAndReplyBot()
        rb.cur = './path'
        assert isinstance(rb.cur, sqlite3.Cursor)

    def test_connect_memory(self, amend_sqlite3_connect):
        rb = RedditScanAndReplyBot()
        rb.cur = ":memory:"
        assert isinstance(rb.cur, sqlite3.Cursor)

    def test_sql_conn_failure(self):
        rb = RedditScanAndReplyBot()
        with pytest.raises(Exception) as context:
            rb.cur = 'not a database'

    def test_cursor_not_set(self):
        rb = RedditScanAndReplyBot()
        with pytest.raises(Exception) as context:
            rb.cur