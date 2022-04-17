import praw
import sqlite3

def get_book_db_entry(title: str) -> str:
    con = sqlite3.connect('lightweaver.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM books WHERE title =:title COLLATE NOCASE", {"title": title})
    book_db_entry = cur.fetchone()
    book_db_entry = "Title:\t"+book_db_entry[1]+"\n"+\
                    "Author:\t"+book_db_entry[2]+"\n"+\
                    "ISBN:\t"+book_db_entry[3]+"\n"+\
                    "URI:\t"+book_db_entry[4]+"\n"+\
                    "Desc:\t"+book_db_entry[5]+"\n"
    return book_db_entry

def post_comment(type: int, id: str) -> None:
    r = praw.Reddit("bot1")
    if type == 0:
         post_to_reply_to = r.submission(id=id)
    if type == 1:
        post_to_reply_to = r.comment(id=id)
    print(post_to_reply_to)

def main():
    print(get_book_db_entry("opening the hand of thought"))

if __name__ == "__main__":
    main()