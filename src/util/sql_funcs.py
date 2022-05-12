import sqlite3
from urllib.request import pathname2url

def get_sql_cursor(db_str: str) -> sqlite3.Cursor:
    """
    Takes a db_string. Either an existant database or :memory: is acceptable.
    :param db_str: string referencing path to a file, or ":memory:".
    :raises Exception: if database is not found at given location.
    """
    if db_str == ":memory:":
        dburi = ":memory:"
    else:
        dburi = 'file:{}?mode=rw'.format(pathname2url(db_str))

    try:
        conn = sqlite3.connect(dburi, uri=True)
        cur = conn.cursor()
        return cur
    except sqlite3.OperationalError:
        raise Exception(f"Database not found at {dburi}. Please confirm database exists and is read/write accessible.")

def get_books(session) -> list:
    """
    Takes a SQLite3 cursor, retrieves the titles of books in the books table.

    :param session: A sqlite3.Cursor object.
    :returns books: a list(str) of book titles. Titles are all lower case.
    :raises sqlite3.ProgrammingError: if table is not found.
    """
    session.execute('SELECT title FROM books')
    books = session.fetchall()
    books = list({str(book[0]).lower() for book in books})
    return books

def get_opted_in_users(session):
    """ 
    Connects to the sql database and returns a list of opted in users who wish to
    receive repies from this bot.
    
    :param session: sqlite3.Cursor
    :returns opted_in_users: list of usernames as list[str]
    :raises sqlite3.ProgrammingError: if table is not found.
    """
    session.execute('SELECT reddit_username FROM opted_in_users')
    opted_in_users = session.fetchall()
    opted_in_users = list({str(user[0]).lower() for user in opted_in_users})
    return opted_in_users

def update_opted_in_users(session, username: str):
    """
    Takes a cursor and a reddit Username, adds that username to the opted in users database if not already present.
    :param session: Sqlite3.Cursor
    :param username: Reddit username (str)
    :raises ValueError: If user is already in database.
    """
    current_users = get_opted_in_users(session)
    if username in current_users:
        raise ValueError("User is already in opted in list.")
    else:
        session.execute('INSERT INTO opted_in_users (reddit_username) VALUES (?)', [username])
        session.connection.commit()

def get_replied_entries(session):
    """
    Takes sqlite3 cursor object, returns list of fullname reddit IDs that the bot has 
    already replied to.
    
    :param session: sqlite3.Cursor
    :returns replied_entries: list(str)
    :raises sqlite3.ProgrammingError: if table is not found.
    """
    session.execute("SELECT reddit_id FROM replied_entries")
    already_replied = session.fetchall()
    already_replied = list({str(entry[0]) for entry in already_replied})
    return already_replied

def update_replied_entries_table(session, fullname: str) -> None:
    """
    Takes a cursor and a reddit post fullname, adds that fullname to the opted in users table if not already present.
    :param session: Sqlite3.Cursor
    :param username: Reddit fullname (str)
    :raises ValueError: If post fullname is already in database.
    """
    current_posts = get_replied_entries(session)
    if fullname in current_posts:
        raise ValueError("Post fullname is already in replied posts list. This should never happen. The application may have double posted.")
    else:
        session.execute("INSERT INTO replied_entries (reddit_id) VALUES (?)", [fullname])
        session.connection.commit()

def get_book_db_entry(session, title: str) -> dict:
    """
    Accepts a title of a book. Returns the database entry for that book in a formatted block.
    
    :param title: str
    :returns: str
    :raises KeyError: If title is not found in database.
    """
    session.execute("SELECT * FROM books WHERE title = ? COLLATE NOCASE", [title])
    book_db_entry = session.fetchone()
    book_data = {}

    if book_db_entry is None:
        raise KeyError("Title not found in database.")

    book_data['title'] = book_db_entry[1]
    book_data['author'] = book_db_entry[2]
    book_data['isbn'] = book_db_entry[3]
    book_data['uri'] = book_db_entry[4]
    book_data['desc'] = book_db_entry[5]

    return book_data