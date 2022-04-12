import praw
import sqlite3

r = praw.Reddit("bot1")
con = sqlite3.connect('lightweaver.db')
cur = con.cursor()
subreddit = r.subreddit("lightweaver_bot")

books = cur.execute('SELECT title FROM books')

for submission in subreddit.hot(limit=5):
    for book in books:
        book = book[0]
        print(book)
        if book in submission.title:
            print(f"Keyword found in {submission.title} {submission.id}")
        if book in submission.selftext:
            print(f"Keyword found in self text of {submission.title} {submission.id}")
        for comment in submission.comments:
            if book in comment.body:
                print(f"Keyword found in comment {comment.body} {comment.id} of submission {submission.title} {submission.id}")