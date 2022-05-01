import praw #type: ignore
import sqlite3

DATABASE='lightweaver.db'
BOT_PRAW_NAME = 'lightweaver'
URL = "https://www.reddit.com/r/lightweaver_bot/comments/udh3ao/comment_in_this_thread_if_you_would_like_to_optin/"

def main():
    users = get_opt_ins(URL)
    refresh_opt_in_table(users)

def get_opt_ins(url: str) -> list:
    """
    Accepts a given URL of a reddit thread.
    Retrieves the set of all usernames present in this thread and returns them as a list of strings.

    :param url: the URL of the thread to scrape.
    :returns: list(str(username))
    """
    r = praw.Reddit(BOT_PRAW_NAME)
    opt_in_thread = r.submission(url=url)
    opted_in_users = []

    for comment in opt_in_thread.comments:
        opted_in_users.append(str(comment.author))

    opted_in_users =  list({str(user) for user in opted_in_users}) #de-duplicate

    return opted_in_users

def refresh_opt_in_table(users: list) -> None:
    """
    Accepts a list of usernames as strings.
    Drops the existing entries from the database and re-populates the table.
    
    :param users: list(str(username))
    """
    
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute("DELETE FROM opted_in_users")
    for user in users:
        cur.execute("INSERT INTO opted_in_users (reddit_username) VALUES (?)", [user])
    
    con.commit()

if __name__ == '__main__':
    main()