# Reddit Scan And Reply Bot

This program connects to reddit, scans for a list of books titles, and where found, posts a reply with information on the relevant book(s) mentioned.
This program will only reply to users who have opted into this bot by posting in a reddit thread specified in the configuration file.

Usage:

1. Create `config.ini` in a directory accessible by the program.
2. Run the program with the --initalize switch to initialize the sqlite3 database. (`python -m RedditScanAndReplyBot.py --config <config.ini> --initalize`)
3. Enter the relevant information into the `books` table of the sqlite3 database. (See below)
3. Run the program using `python -m RedditScanAndReplyBot.py --config <config.ini>`

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
opt_in_thread = https://www.reddit.com/r/<subreddit>/comments/<uniquethreadid>/<threadtitle>

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
`opt_in_thread` should contain the reddit thread that users can reply to in order to subscribe to this bot and receive replies. This URL can be obtained from the reddit "Permalink" function on the given thread.

The sqlite3 database information is under the [DATABASE] header. If this file does not exist, the program will create one and initialize it. The user must manually add appropriate information to the "books" table.

## Sqlite3 Database Configuration

The schema for this database is as follows.

```
CREATE TABLE books(id integer PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, author text NOT NULL, isbn text NOT NULL, uri text, summary text not null);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE replied_entries (id integer PRIMARY KEY AUTOINCREMENT, reddit_id TEXT UNIQUE NOT NULL, reply_succeeded_bool integer NOT NULL);
CREATE TABLE opted_in_users (id integer PRIMARY KEY AUTOINCREMENT, reddit_username TEXT UNIQUE NOT NULL);
```

The replied_entries table populates automatically as the bot posts.
The opted_in_users table should contain a list of reddit usernames of users who have consented to have this bot reply to their posts.
The books table contains important information on the books to scan. Summary is current not ever posted due to text length constraints.

The user must manually populate the 'books' table. Opted_in_users and replied_entries are managed by the application.

### To populate the books table:

1. Determine the rows to be added to the database. Each row must contain the following information:

Title - The book's title.
Author - The book's author.
ISBN - The book's ISBN. Either ISBN 10 or 13 may be used.
URI - The book's publisher's listing. I.e. the publisher's webpage describing the book, its contents, where it can be bought, etc. It is recommended to NOT use merchant links (i.e. Amazon, etc.) for this entry, as these change frequently.
Summary - A text description of the book. This is stored in the internal database and not printed, at present.

2. Connect to the database using sqlite3. `sqlite3 <database.db>`
3. Perform an INSERT INTO books query. `INSERT INTO books (title, author, isbn, uri, summary) VALUES ("<title>", "<author>", "<isbn>", "<uri>", "<summary>");`

You will need to escape any single quotes "'" with an additional single quote before it, e.g. "reader's" becomes "reader''s". If any lines have line breaks in them, sqlite3 will preserve these breaks when storing and returning data, and they will be printed. E.g. in the summary field.

4. Once finished entering INSERT statements, submit a `commit;` statement to write all transactions to the database on disk.
5. type `.q` to exit sqlite3.