from importlib.resources import path
import os
import sqlite3
import pytest 
from reddit_scan_and_reply_bot.RedditScanAndReplyBot import RedditScanAndReplyBot
from reddit_scan_and_reply_bot.util.sql_funcs import add_opted_in_user, create_database, get_sql_cursor, get_books, get_opted_in_users, get_replied_entries, update_opted_in_users, update_replied_entries_table, get_book_db_entry # type: ignore

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
        add_opted_in_user(cur, "test_author3")
        result = sorted(get_opted_in_users(cur))
        expected_result = 'test_author3'
        assert expected_result in result

    def test_add_opted_in_user_duplicate(self, amend_sqlite3_connect):
        conn = sqlite3.connect('./path')
        cur = conn.cursor()
        with pytest.raises(sqlite3.IntegrityError) as context:
            add_opted_in_user(cur, "test_author2")  
        
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

    def test_create_database_success(self, amend_sqlite3_connect, amend_os_path_isfile):
        if os.path.isfile('./tests/test_db_1'):
            os.remove('./tests/test_db_1')
        create_database('./tests/test_db_1')
        conn = sqlite3.connect('./tests/test_db_1')
        cur = conn.cursor()
        cur.execute("PRAGMA table_info('books')")
        books = cur.fetchall()
        expected_book_columns = [(0, 'id', 'integer', 0, None, 1),
                                (1, 'title', 'TEXT', 1, None, 0),
                                (2, 'author', 'text', 1, None, 0),
                                (3, 'isbn', 'text', 1, None, 0),
                                (4, 'uri', 'text', 0, None, 0),
                                (5, 'summary', 'text', 1, None, 0)]
        cur.execute("PRAGMA table_info('opted_in_users')")
        oiu = cur.fetchall()
        expected_opted_in_users = [(0, 'id', 'integer', 0, None, 1),
                                (1, 'reddit_username', 'TEXT', 1, None, 0)]
        cur.execute("PRAGMA table_info('replied_entries')")
        re = cur.fetchall()
        expected_replied_entries = [(0, 'id', 'integer', 0, None, 1),
                                    (1, 'reddit_id', 'TEXT', 1, None, 0),
                                    (2, 'reply_succeeded_bool', 'integer', 1, None, 0)]
        assert expected_book_columns == books
        assert expected_opted_in_users == oiu
        assert expected_replied_entries == re
        os.remove('./tests/test_db_1')

    def test_create_database_nonsql_file(self):
        open('./tests/not-a-db','a').close()
        with pytest.raises(sqlite3.OperationalError) as context:
            create_database('./tests/not-a-db')
        os.remove('./tests/not-a-db')

    @pytest.mark.usefixtures("setup_test_db")
    def test_create_database_wrongsql_database(self):
        with pytest.raises(sqlite3.ProgrammingError) as context:
            create_database('./tests/wrong_schema.db')
        os.remove('./tests/wrong_schema.db')

    @pytest.mark.usefixtures("setup_test_db")
    def test_create_database_db_already_exists(self, amend_sqlite3_connect, amend_os_path_isfile):
        create_database('./tests/test.db')
        conn = sqlite3.connect('./tests/test.db')
        cur = conn.cursor()
        cur.execute("PRAGMA table_info('books')")
        books = cur.fetchall()
        expected_book_columns = [(0, 'id', 'integer', 0, None, 1),
                                (1, 'title', 'TEXT', 1, None, 0),
                                (2, 'author', 'text', 1, None, 0),
                                (3, 'isbn', 'text', 1, None, 0),
                                (4, 'uri', 'text', 0, None, 0),
                                (5, 'summary', 'text', 1, None, 0)]
        cur.execute("PRAGMA table_info('opted_in_users')")
        oiu = cur.fetchall()
        expected_opted_in_users = [(0, 'id', 'integer', 0, None, 1),
                                (1, 'reddit_username', 'TEXT', 1, None, 0)]
        cur.execute("PRAGMA table_info('replied_entries')")
        re = cur.fetchall()
        expected_replied_entries = [(0, 'id', 'integer', 0, None, 1),
                                    (1, 'reddit_id', 'TEXT', 1, None, 0),
                                    (2, 'reply_succeeded_bool', 'integer', 1, None, 0)]
        assert expected_book_columns == books
        assert expected_opted_in_users == oiu
        assert expected_replied_entries == re

    @pytest.mark.usefixtures("setup_test_db")
    def test_update_opted_in_user_simple_add(self, amend_sqlite3_connect):
        conn = sqlite3.connect('./path')
        cur = conn.cursor()
        usernames = []
        usernames.append('test_author1')
        usernames.append('test_author2')
        usernames.append("user1")
        usernames.append("user2")
        update_opted_in_users(cur, usernames)
        cur.execute('Select * from opted_in_users')
        results = cur.fetchall()
        expected_results = [(1, 'test_author1'), 
                            (2, 'test_author2'),
                            (3, 'user1'),
                            (4, 'user2')]
        assert results == expected_results

    @pytest.mark.usefixtures("setup_test_db")
    def test_update_opted_in_user_remove_user(self, amend_sqlite3_connect):
        conn = sqlite3.connect('./path')
        cur = conn.cursor()
        usernames = []
        usernames.append("test_author1")
        update_opted_in_users(cur, usernames)
        cur.execute('Select * from opted_in_users')
        results = cur.fetchall()
        expected_results = [(1, 'test_author1')]
        assert results == expected_results

    @pytest.mark.usefixtures("setup_test_db")
    def test_update_opted_in_user_add_and_remove(self, amend_sqlite3_connect):
        conn = sqlite3.connect('./path')
        cur = conn.cursor()
        usernames = []
        usernames.append("test_author1")
        usernames.append("user1")
        update_opted_in_users(cur, usernames)
        cur.execute('Select * from opted_in_users')
        results = cur.fetchall()
        expected_results = [(1, 'test_author1'),
                            (3, 'user1')]
        assert results == expected_results

    @pytest.mark.usefixtures("setup_test_db")
    def test_update_opted_in_user_no_change(self, amend_sqlite3_connect):
        conn = sqlite3.connect('./path')
        cur = conn.cursor()
        usernames = []
        usernames.append("test_author1")
        usernames.append("test_author2")
        update_opted_in_users(cur, usernames)
        cur.execute('Select * from opted_in_users')
        results = cur.fetchall()
        expected_results = [(1, 'test_author1'),
                            (2, 'test_author2')]
        assert results == expected_results

    @pytest.mark.usefixtures("setup_test_db")
    def test_update_opted_in_user_blank_list(self, amend_sqlite3_connect):
        conn = sqlite3.connect('./path')
        cur = conn.cursor()
        usernames = []
        update_opted_in_users(cur, usernames)
        cur.execute('Select * from opted_in_users')
        results = cur.fetchall()
        expected_results = []
        assert results == expected_results