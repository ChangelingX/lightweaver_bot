from importlib.resources import path
import sqlite3
import pytest 
from reddit_scan_and_reply_bot.RedditScanAndReplyBot import RedditScanAndReplyBot
from reddit_scan_and_reply_bot.util.sql_funcs import get_sql_cursor, get_books, get_opted_in_users, get_replied_entries, update_opted_in_users, update_replied_entries_table, get_book_db_entry # type: ignore

class Test_SQL_functionality:
    def test_get_sql_cursor(self, amend_sqlite3_connect):
        cur = get_sql_cursor('./path')
        assert isinstance(cur, sqlite3.Cursor)

    def test_get_sql_cursor_non_existant_db(self, amend_sqlite3_connect):
        with pytest.raises(Exception) as context:
            cur = get_sql_cursor('./not a database')

    @pytest.mark.usefixtures('setup_test_db')
    def test_get_books(self, amend_sqlite3_connect):
        conn = sqlite3.connect('./path')
        cur = conn.cursor()
        result = sorted(get_books(cur))
        expected_result = sorted(['book1', 'book2', 'book3'])
        assert result == expected_result

    @pytest.mark.usefixtures('setup_test_db')
    def test_get_opted_in_users(self, amend_sqlite3_connect):
        conn = sqlite3.connect('./path')
        cur = conn.cursor()
        result = sorted(get_opted_in_users(cur))
        expected_result = sorted(['test_author1','test_author2'])
        assert result == expected_result

    def test_add_opted_in_user(self, amend_sqlite3_connect):
        conn = sqlite3.connect('./path')
        cur = conn.cursor()
        update_opted_in_users(cur, "test_author3")
        result = sorted(get_opted_in_users(cur))
        expected_result = 'test_author3'
        assert expected_result in result

    def test_add_opted_in_user_duplicate(self, amend_sqlite3_connect):
        conn = sqlite3.connect('./path')
        cur = conn.cursor()
        with pytest.raises(ValueError) as context:
            update_opted_in_users(cur, "test_author2")  
        
    @pytest.mark.usefixtures('setup_test_db')
    def test_get_replied_posts(self, amend_sqlite3_connect):
        conn = sqlite3.connect('./path')
        cur = conn.cursor()
        result = sorted(get_replied_entries(cur))
        expected_result = sorted(['c1', 's1'])
        assert result == expected_result

    @pytest.mark.usefixtures('setup_test_db')
    def test_add_replied_post(self, amend_sqlite3_connect):
        conn = sqlite3.connect('./path')
        cur = conn.cursor()
        update_replied_entries_table(cur, "t1_c2", True)
        result = sorted(get_replied_entries(cur))
        expected_result = 'c2'
        assert expected_result in result

    @pytest.mark.usefixtures('setup_test_db')
    def test_add_replied_post_duplicate(self, amend_sqlite3_connect):
        conn = sqlite3.connect('./path')
        cur = conn.cursor()
        with pytest.raises(ValueError) as context:
            update_replied_entries_table(cur, "t1_c1", True)
        
    def test_get_book_database_entry(self, amend_sqlite3_connect):
        conn = sqlite3.connect('./path')
        cur = conn.cursor()
        result = get_book_db_entry(cur, 'book1')
        expected_result = {'title': 'book1', 'author': 'author1', 'isbn': 'isbn1', 'uri': 'url1', 'desc': 'sum1'}
        assert result == expected_result