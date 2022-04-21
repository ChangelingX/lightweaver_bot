import praw
import sqlite3

def get_book_db_entry(title: str) -> str:
    con = sqlite3.connect('lightweaver.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM books WHERE title =:title COLLATE NOCASE", {"title": title})
    book_db_entry = cur.fetchone()
    book_db_entry = "Title:\t"+book_db_entry[1]+"\n\n"+\
                    "Author:\t"+book_db_entry[2]+"\n\n"+\
                    "ISBN:\t"+book_db_entry[3]+"\n\n"+\
                    "URI:\t"+book_db_entry[4]+"\n\n"+\
                    "Desc:\t"+book_db_entry[5]+"\n"
    return book_db_entry

def post_comment(type: int, id: str, title: str) -> None:
    r = praw.Reddit("bot1")
    con = sqlite3.connect('lightweaver.db')
    cur = con.cursor()
    if type == 0:
         post_to_reply_to = r.submission(id=id)
    if type == 1:
        post_to_reply_to = r.comment(id=id)
    #print(post_to_reply_to)
    cur.execute("SELECT reddit_id FROM replied_entries WHERE reddit_id = ?", [post_to_reply_to.id])
    already_replied = cur.fetchone()
    posted_reply = None
    if already_replied is None:
        posted_reply = post_to_reply_to.reply(get_book_db_entry(title))
    if posted_reply is not None:
        cur.execute("SELECT MAX(id) FROM replied_entries")
        max_id = cur.fetchone()
        next_id = max_id[0] + 1
        cur.execute("INSERT INTO replied_entries (id, reddit_id) VALUES (?, ?)", [next_id, post_to_reply_to.id])
    con.commit()

def main():
    print(get_book_db_entry("opening the hand of thought"))

if __name__ == "__main__":
    main()