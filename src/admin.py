import praw
import sqlite3

def main():
    url = "https://www.reddit.com/r/lightweaver_bot/comments/udh3ao/comment_in_this_thread_if_you_would_like_to_optin/"
    users = get_opt_ins(url)
    refresh_opt_in_table(users)

def get_opt_ins(url: str) -> list:
    """
    Accepts a given URL of a reddit thread.
    Retrieves the set of all usernames present in this thread and returns them as a list of strings.

    :param url: the URL of the thread to scrape.
    :returns: list(str(username))
    """
    r = praw.Reddit("bot1")
    opt_in_thread = r.submission(url=url)
    opted_in_users = []

    for comment in opt_in_thread.comments:
        opted_in_users.append(str(comment.author))

    opted_in_users =  list(dict.fromkeys(opted_in_users)) # de-duplicate list

    return opted_in_users

def refresh_opt_in_table(users: list) -> None:
    """
    Accepts a list of usernames as strings.
    Drops the existing entries from the database and re-populates the table.
    
    :param users: list(str(username))
    """
    
    con = sqlite3.connect('lightweaver.db')
    cur = con.cursor()
    cur.execute("DELETE FROM opted_in_users WHERE id >= 1")
    for user in users:
        cur.execute("SELECT MAX(id) FROM opted_in_users")
        max_id = cur.fetchone()
        next_id = max_id[0] + 1
        cur.execute("INSERT INTO opted_in_users (id, reddit_username) VALUES (?, ?)", [next_id, user])
    
    con.commit()

if __name__ == '__main__':
    main()