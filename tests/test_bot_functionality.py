import re
from unittest.mock import Mock
import pytest
import sqlite3 
from src.reddit_scan_and_reply_bot.RedditScanAndReplyBot import RedditScanAndReplyBot
from conftest import MockComment, MockCommentForest, MockReddit
from src.reddit_scan_and_reply_bot.util.sql_funcs import get_opted_in_users, get_replied_entries

class Test_BotFunctionality:

    def test_scan_config_file(self, amend_configparser_read, amend_os_path_isfile):
        rb = RedditScanAndReplyBot.from_file('./path')
        result = rb.configs
        expected_result = {
            'DATABASE': {
                'database_name': "./tests/test.db"
            }, 
            'PRAW': {
                'client_id': "test_client_id", 
                'client_secret': "test_client_secret", 
                'password': "test_password", 
                'username': "test_username", 
                'user_agent': "test_user_agent",
                'subreddits': "mock_subreddit1+mock_subreddit2+quarantined_subreddit",
                'bot_subreddit': 'mock_botsubreddit',
                'opt_in_thread': 'https://www.mockreddit.com/r/mock_botsubreddit/comments/6/opt_in_thread/'
            }
        }
        assert result == expected_result

    def test_scan_config_invalid_file_bad_PRAW_section(self):
        with pytest.raises(Exception) as context:
            rb = RedditScanAndReplyBot.from_file('./tests/invlaid_config_bad_PRAW.ini')

    def test_scan_config_invalid_file_bad_DATABASE_section(self):
        with pytest.raises(Exception) as context:
            rb = RedditScanAndReplyBot.from_file('./tests/invlaid_config_bad_DATABASE.ini')
            
    def test_scan_config_invalid_file_missing_section(self):
        with pytest.raises(Exception) as context:
            rb = RedditScanAndReplyBot.from_file('./tests/invlaid_config_missing_section.ini')
                    
    def test_scan_config_file_not_found(self):
        with pytest.raises(Exception) as context:
            rb = RedditScanAndReplyBot.from_file('not a file')
          
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

    def test_connect_reddit(self, mock_reddit):
        rb = RedditScanAndReplyBot()
        reddit_config = {
            'client_id':'test_client_id',
            'client_secret':'test_client_secret',
            'password':'test_password',
            'username':'test_username',
            'user_agent':'test_user_agent',
            'subreddits':'mock_subreddit1+mock_subreddit2+quarantined_subreddit'
        }
        rb.reddit = reddit_config
        assert isinstance(rb.reddit, MockReddit)

    def test_reddit_not_set(self):
        rb = RedditScanAndReplyBot()
        with pytest.raises(Exception) as context:
            rb.reddit

    def test_setup(self, mock_reddit, amend_configparser_read, amend_os_path_isfile, amend_sqlite3_connect):
        rb = RedditScanAndReplyBot.from_file('./path')
        rb.setup()

    def test_setup_missing_database_config(self, amend_configparser_read):
        rb = RedditScanAndReplyBot()
        rb._praw_config = {
            'client_id' : 'test_client_id',
            'client_secret': 'test_client_secret',
            'password':'test_password',
            'username':'test_username',
            'user_agent':'test_user_agent',
            'subreddits':'mock_subreddit1+mock_subreddit2+quarantined_subreddit'
            }
        with pytest.raises(Exception) as context:
            rb.setup()

    def test_setup_missing_praw_config(self):
        rb = RedditScanAndReplyBot()
        rb._database_config = {'DATABASE':{'database_name':'./path'}}
        with pytest.raises(Exception) as context:
            rb.setup()

    def test_setup_malformed_praw_config(self):
        rb = RedditScanAndReplyBot()
        rb._praw_config = {
            'client_id' : 'test_client_id',
            'missing_section': 'test_client_secret',
            'password':'test_password',
            'username':'test_username',
            'user_agent':'test_user_agent',
            'subreddits':'mock_subreddit1+mock_subreddit2+quarantined_subreddit'
            }
        rb._database_config = {'DATABASE':{'database_name':'./path'}}
        with pytest.raises(Exception) as context:
            rb.setup()

    @pytest.mark.usefixtures("setup_test_db")
    def test_get_formatted_post_body(self, mock_reddit, amend_os_path_isfile, amend_configparser_read, amend_sqlite3_connect):
        rb = RedditScanAndReplyBot().from_file('./path')
        rb.setup()
        post_text = rb.get_formatted_post_body(['book1', 'book2'])
        expected_regex = r'Hello, I am \w*\. I am a bot that posts information on books that you have mentioned.\n\n------------------------\n\n(Title:  \w*\n\nAuthor: \w*\n\nISBN:   \w*\n\nURI:    \w*\n\n------------------------\n\n)+\nThis post was made by a bot.\nFor more information, or to give feedback or suggestions, please visit \/r\/\w*\.'
        assert re.match(expected_regex, post_text)

    @pytest.mark.usefixtures("setup_test_db")
    def test_scrape_reddit(self, mock_reddit, amend_sqlite3_connect):
        rb = RedditScanAndReplyBot()
        rb._praw_config = {
            'client_id' : 'test_client_id',
            'client_secret': 'test_client_secret',
            'password':'test_password',
            'username':'test_username',
            'user_agent':'test_user_agent',
            'subreddits':'mock_subreddit1+mock_subreddit2+quarantined_subreddit',
            'bot_subreddit': 'mock_botsubreddit'
            }
        rb._database_config = {'database_name':'./path'}
        rb.setup()
        rb.reddit.setup_reddit()
        pre_scrape_replied_entries = get_replied_entries(rb.cur)
        pre_scrape_user_posts = rb.reddit.user.me().comments.new()

        rb.scrape_reddit()
        post_scrape_1_replied_entries = get_replied_entries(rb.cur)
        post_scrape_1_user_posts = rb.reddit.user.me().comments.new()
        
        replied_diff = set(post_scrape_1_replied_entries).difference(set(pre_scrape_replied_entries))
        user_post_diff = set(post_scrape_1_user_posts).difference(set(pre_scrape_user_posts))
        expected_replied_diff = {'s3', 'c5', 'c3', 'c4', 'c6'}
        expected_post_diff = {
                            MockComment(None, None, 't1_c11', None, None), 
                            MockComment(None, None, 't1_c13', None, None),
                            MockComment(None, None, 't1_c12', None, None)
                            }
        assert expected_post_diff == user_post_diff
        assert expected_replied_diff == replied_diff
        rb.scrape_reddit()

        post_scrape_2_replied_entries = get_replied_entries(rb.cur)
        post_scrape_2_user_posts = rb.reddit.user.me().comments.new()

        replied_diff_2 = set(post_scrape_2_replied_entries).difference(set(post_scrape_1_replied_entries))
        user_post_diff_2 = set(post_scrape_2_user_posts).difference(set(post_scrape_1_user_posts))
        assert len(replied_diff_2) == 0
        assert len(user_post_diff_2) == 0

    @pytest.mark.usefixtures("setup_test_db")
    def test_update_opted_in_users(self, mock_reddit, amend_os_path_isfile, amend_configparser_read, amend_sqlite3_connect):
        rb = RedditScanAndReplyBot()
        rb._praw_config = {
            'client_id' : 'test_client_id',
            'client_secret': 'test_client_secret',
            'password':'test_password',
            'username':'test_username',
            'user_agent':'test_user_agent',
            'subreddits':'mock_subreddit1+mock_subreddit2+quarantined_subreddit',
            'bot_subreddit': 'mock_botsubreddit',
            'opt_in_thread': 'https://www.mockreddit.com/r/mock_botsubreddit/comments/6/opt_in_thread/'
            }
        rb._database_config = {'database_name':'./path'}
        rb.setup()
        rb.reddit.setup_reddit()
        rb.repopulate_opted_in_users()
        results = sorted(get_opted_in_users(rb.cur))
        expected_results = sorted(['test_author1', 'test_author2', 'test_author3', 'test_author4'])
        assert results == expected_results

    @pytest.mark.usefixtures("setup_test_db")
    def test_update_opted_in_users_unenroll(self, mock_reddit, amend_os_path_isfile, amend_configparser_read, amend_sqlite3_connect):
        rb = RedditScanAndReplyBot()
        rb._praw_config = {
            'client_id' : 'test_client_id',
            'client_secret': 'test_client_secret',
            'password':'test_password',
            'username':'test_username',
            'user_agent':'test_user_agent',
            'subreddits':'mock_subreddit1+mock_subreddit2+quarantined_subreddit',
            'bot_subreddit': 'mock_botsubreddit',
            'opt_in_thread': 'https://www.mockreddit.com/r/mock_botsubreddit/comments/6/opt_in_thread/'
            }
        rb._database_config = {'database_name':'./path'}
        rb.setup()
        rb.reddit.setup_reddit()
        rb.cur.execute('INSERT INTO opted_in_users (reddit_username) VALUES (?)',['test_author3'])
        rb.cur.execute('INSERT INTO opted_in_users (reddit_username) VALUES (?)',['test_author4'])
        rb.cur.execute('INSERT INTO opted_in_users (reddit_username) VALUES (?)',['test_author5'])
        rb.cur.connection.commit()
        rb.repopulate_opted_in_users()
        results = sorted(get_opted_in_users(rb.cur))
        expected_results = sorted(['test_author1', 'test_author2', 'test_author3', 'test_author4'])
        assert results == expected_results

    @pytest.mark.usefixtures("setup_test_db")
    def test_update_opted_in_users_no_change(self, mock_reddit, amend_os_path_isfile, amend_configparser_read, amend_sqlite3_connect):
        rb = RedditScanAndReplyBot()
        rb._praw_config = {
            'client_id' : 'test_client_id',
            'client_secret': 'test_client_secret',
            'password':'test_password',
            'username':'test_username',
            'user_agent':'test_user_agent',
            'subreddits':'mock_subreddit1+mock_subreddit2+quarantined_subreddit',
            'bot_subreddit': 'mock_botsubreddit',
            'opt_in_thread': 'https://www.mockreddit.com/r/mock_botsubreddit/comments/6/opt_in_thread/'
            }
        rb._database_config = {'database_name':'./path'}
        rb.setup()
        rb.reddit.setup_reddit()
        rb.cur.execute('INSERT INTO opted_in_users (reddit_username) VALUES (?)',['test_author3'])
        rb.cur.execute('INSERT INTO opted_in_users (reddit_username) VALUES (?)',['test_author4'])
        rb.cur.connection.commit()
        rb.repopulate_opted_in_users()
        results = sorted(get_opted_in_users(rb.cur))
        expected_results = sorted(['test_author1', 'test_author2', 'test_author3', 'test_author4'])
        assert results == expected_results

    @pytest.mark.usefixtures("setup_test_db")
    def test_update_opted_in_users_thread_not_found(self, mock_reddit, amend_os_path_isfile, amend_configparser_read, amend_sqlite3_connect):
        rb = RedditScanAndReplyBot()
        rb._praw_config = {
            'client_id' : 'test_client_id',
            'client_secret': 'test_client_secret',
            'password':'test_password',
            'username':'test_username',
            'user_agent':'test_user_agent',
            'subreddits':'mock_subreddit1+mock_subreddit2+quarantined_subreddit',
            'bot_subreddit': 'mock_botsubreddit',
            'opt_in_thread': 'https://www.mockreddit.com/r/mock_botsubreddit/comments/8/opt_in_thread/'
            }
        rb._database_config = {'database_name':'./path'}
        rb.setup()
        rb.reddit.setup_reddit()
        with pytest.raises(Exception) as context:
            rb.repopulate_opted_in_users()

    @pytest.mark.usefixtures('setup_test_db')
    def test_updated_replied_entries_simple(self, mock_reddit, amend_os_path_isfile, amend_sqlite3_connect, amend_configparser_read):
        rb = RedditScanAndReplyBot()
        rb._praw_config = {
            'client_id' : 'test_client_id',
            'client_secret': 'test_client_secret',
            'password':'test_password',
            'username':'test_username',
            'user_agent':'test_user_agent',
            'subreddits':'mock_subreddit1+mock_subreddit2+quarantined_subreddit',
            'bot_subreddit': 'mock_botsubreddit',
            'opt_in_thread': 'https://www.mockreddit.com/r/mock_botsubreddit/comments/8/opt_in_thread/'
            }
        rb._database_config = {'database_name':'./path'}
        rb.setup()
        rb.reddit.setup_reddit()
        submission = rb.reddit.get_submissions()[1]
        rb.cur.execute("select * from replied_entries")
        before_reply = rb.cur.fetchall()
        submission.reply("test")
        rb.cur.execute("select * from replied_entries")
        after_reply = rb.cur.fetchall()
        rb.repopulate_replied_entries()
        rb.cur.execute("select * from replied_entries")
        after_repopulate = rb.cur.fetchall()
        s = set(after_repopulate)
        s2 = set(after_reply)
        diff = list(s ^ s2)
        assert before_reply == after_reply
        assert diff == [(3, 's2', 1)]

    @pytest.mark.usefixtures('setup_test_db')
    def test_repopulate_replied_entries_deleted_reply(self, mock_reddit, amend_os_path_isfile, amend_sqlite3_connect, amend_configparser_read):
        rb = RedditScanAndReplyBot()
        rb._praw_config = {
            'client_id' : 'test_client_id',
            'client_secret': 'test_client_secret',
            'password':'test_password',
            'username':'test_username',
            'user_agent':'test_user_agent',
            'subreddits':'mock_subreddit1+mock_subreddit2+quarantined_subreddit',
            'bot_subreddit': 'mock_botsubreddit',
            'opt_in_thread': 'https://www.mockreddit.com/r/mock_botsubreddit/comments/8/opt_in_thread/'
            }
        rb._database_config = {'database_name':'./path'}
        rb.setup()
        rb.reddit.setup_reddit()
        submission = rb.reddit.get_submissions()[1]
        submission.reply("test")
        rb.repopulate_replied_entries()
        rb.cur.execute("SELECT * FROM replied_entries")
        after_first_repopulate = rb.cur.fetchall()
        rb.reddit.user.me().comments.remove_comment('t1_c11')
        rb.repopulate_replied_entries()
        rb.cur.execute("SELECT * FROM replied_entries")
        after_second_repopulate = rb.cur.fetchall()
        assert after_first_repopulate == after_second_repopulate

    @pytest.mark.usefixtures('setup_test_db')
    def test_repopulate_replied_entries_two_new_entries(self, mock_reddit, amend_os_path_isfile, amend_sqlite3_connect, amend_configparser_read):
        rb = RedditScanAndReplyBot()
        rb._praw_config = {
            'client_id' : 'test_client_id',
            'client_secret': 'test_client_secret',
            'password':'test_password',
            'username':'test_username',
            'user_agent':'test_user_agent',
            'subreddits':'mock_subreddit1+mock_subreddit2+quarantined_subreddit',
            'bot_subreddit': 'mock_botsubreddit',
            'opt_in_thread': 'https://www.mockreddit.com/r/mock_botsubreddit/comments/8/opt_in_thread/'
            }
        rb._database_config = {'database_name':'./path'}
        rb.setup()
        rb.reddit.setup_reddit()
        rb.cur.execute("SELECT * FROM replied_entries")
        before_repopulate = rb.cur.fetchall()
        submission = rb.reddit.get_submissions()[1]
        submission.reply("test")
        submission = rb.reddit.get_submissions()[2]
        submission.reply("test2")
        rb.repopulate_replied_entries()
        rb.cur.execute("SELECT * FROM replied_entries")
        after_repopulate = rb.cur.fetchall()
        diff = set(before_repopulate) ^ set(after_repopulate)
        assert sorted(diff) == sorted([(3, 's3', 1), (4, 's2', 1)])