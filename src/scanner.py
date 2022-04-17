import praw
import sqlite3
import poster

def main():
    r = praw.Reddit("bot1")
    con = sqlite3.connect('lightweaver.db')
    cur = con.cursor()
    subreddit = r.subreddit("lightweaver_bot")

    cur.execute('SELECT title FROM books')
    books = cur.fetchall()

    for submission in subreddit.top("all"):
        print(submission.title)
        for book in books:
            book = str(book[0]).lower()
            print(book)
            if book in submission.title.lower():
                print(f"Keyword found in {submission.title} {submission.id}")
                poster.post_comment(0,submission.id)
            if book in submission.selftext.lower():
                print(f"Keyword found in self text of {submission.title} {submission.id}")
                poster.post_comment(0,submission.id)
            for comment in submission.comments:
                if book in comment.body.lower():
                    print(f"Keyword found in comment {comment.body} {comment.id} of submission {submission.title} {submission.id}")
                    poster.post_comment(1 ,comment.id)

if __name__ == '__main__':
    main()