import pytest
import sqlite3 
from RedditScanAndReplyBot import RedditScanAndReplyBot
from conftest import MockComment, MockCommentForest, MockReddit

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
                'bot_subreddit': 'mock_botsubreddit'
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

    def test_setup(self, mock_reddit, amend_configparser_read, amend_sqlite3_connect):
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
    def test_get_formatted_post_body(self, mock_reddit, amend_configparser_read, amend_sqlite3_connect):
        rb = RedditScanAndReplyBot().from_file('./path')
        rb.setup()
        post_text = rb.get_formatted_post_body(['book1', 'book2'])
        print(f"\npost body:\n{post_text}")

    # @pytest.mark.usefixtures("setup_test_db")
    # def test_scrape_reddit(self, mock_reddit, amend_sqlite3_connect):
    #     rb = RedditScanAndReplyBot()
    #     rb._praw_config = {
    #         'client_id' : 'test_client_id',
    #         'client_secret': 'test_client_secret',
    #         'password':'test_password',
    #         'username':'test_username',
    #         'user_agent':'test_user_agent',
    #         'subreddits':'mock_subreddit1+mock_subreddit2+quarantined_subreddit'
    #         }
    #     rb._database_config = {'database_name':'./path'}
    #     rb.setup()
    #     rb.reddit.setup_reddit()
    #     rb.scrape_reddit()
    #     rb.scrape_reddit()
