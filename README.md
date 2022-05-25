# Reddit Scan And Reply Bot

This program connects to reddit, scans for a list of books titles, and where found, posts a reply with information on the relevant book(s) mentioned.
This program will only reply to users who have opted into this bot by posting in a reddit thread specified in the configuration file.

Usage:

1. Create `config.ini` in a directory accessible by the program.
2. Create Sqlite3 database file.
3. Run the program using `python -m RedditScanAndReplyBot.py --config <config.ini>

## Config File Formatting

The contents of this file should be as follows:

```
[PRAW]
client_id = test_client_id
client_secret = test_client_secret
password = test_password
username = test_username
user_agent = test_user_agent
subreddits = mock_subreddit1+mock_subreddit2+quarantined_subreddit
bot_subreddit = mock_botsubreddit

[DATABASE]
database_name = ./tests/test.db
```

The PRAW connection information is under the [PRAW] header. The information for these fields can be found at `https://www.reddit.com/prefs/apps`. To generate the reddit supplied information, click "Create an app" at the bottom of the screen. Instructions on how to complete this form to create an app can be found at `https://github.com/reddit-archive/reddit/wiki/OAuth2-Quick-Start-Example#first-steps`. This application can run only as a 'script' type app. It is recommended that you create an account specifically for this bot to use exclusively.

The fields should be populated as such:

Reddit Provided:
`client_id` should contain the client ID.
`client_secret' should be the client secret.
`password` is the password of the account to post under.
`username` is the username of the account to post under.

User Provided:
`subreddits` should be a string of subreddit names, separated by '+' symbols. This is the list of subreddits that the application will monitor.
`bot_subreddit` should be the subreddit that the bot treats as its "home base". This is the bot that other users will post in to provide feedback and suggest changes on the bot.

The sqlite3 database information is under the [DATABASE] header. This must point to a sqlite3 database file that already exists and is configured with the appropriate information.

## Sqlite3 Database Configuration

The schema for this database is as follows.

```
CREATE TABLE books(id integer PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, author text NOT NULL, isbn text NOT NULL, uri text, summary text not null);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE replied_entries (id integer PRIMARY KEY AUTOINCREMENT, reddit_id TEXT NOT NULL, reply_succeeded_bool integer NOT NULL);
CREATE TABLE opted_in_users (id integer PRIMARY KEY AUTOINCREMENT, reddit_username TEXT NOT NULL);
```

The replied_entries table populates automatically as the bot posts.
The opted_in_users table should contain a list of reddit usernames of users who have consented to have this bot reply to their posts.
The books table contains important information on the books to scan. Summary is current not ever posted due to text length constraints.