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
        for book in books:
            books_to_post = []
            book = str(book[0]).lower()
            if book in submission.title.lower():
                books_to_post.append(book) 
                poster.post_comment(submission.id, books_to_post)        
            if book in submission.selftext.lower():
                poster.post_comment(submission.id, book)
            for comment in submission.comments:
                if book in comment.body.lower():
                    poster.post_comment(comment.id, book)

if __name__ == '__main__':
    main()