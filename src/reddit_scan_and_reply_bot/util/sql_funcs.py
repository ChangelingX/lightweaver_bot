import sqlite3
import os
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

def add_opted_in_user(session, username:str):
    """
    Take a cusor and a reddit username, add that username to the opted in users database.
    Raises an exception if the username is not unique.
    :param session: sqlite3.Cursor
    :param username: Reddit username (str)
    :raises Sqlite3.IntegrityError: If username creates non-unique entry.
    """
    try:
        session.execute('INSERT INTO opted_in_users (reddit_username) VALUES (?)', [username])
    except sqlite3.IntegrityError as e:
        raise e
    finally:
        session.connection.commit()

def remove_opted_in_user(session, username:str):
    """
    Takes a sqlite3 cursor and a reddit username, removes the username from the opted_in_users database if found.
    
    :param session: sqlite3.Cursor.
    :param username: reddit username (str)
    :raises sqlite3.IntegrityError: if username not found in table, or if table not found.
    """
    try:
         session.execute('DELETE FROM opted_in_users WHERE (reddit_username) = (?) COLLATE NOCASE',[username.lower()])
    except sqlite3.IntegrityError as e:
        raise e
    finally:
        session.connection.commit()

def update_opted_in_users(session, usernames: list):
    """
    Takes a cursor and a reddit Username, adds that username to the opted in users database if not already present.
    Removes users absent from passed username list.
    :param session: Sqlite3.Cursor
    :param username: Reddit username (str)
    """
    current_users = get_opted_in_users(session) #get current list of users

    for username in usernames: #add new users
        if username not in current_users:
            add_opted_in_user(session, username)

    for current_user in current_users: #remove users not passed.
        if current_user not in usernames:
            remove_opted_in_user(session, current_user)

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

def update_replied_entries_table(session, fullname: str, reply_succeeded: bool) -> None:
    """
    Takes a cursor and a reddit post fullname, adds that fullname to the opted in users table if not already present.
    :param session: Sqlite3.Cursor
    :param username: Reddit fullname (str)
    :raises ValueError: If post fullname is already in database.
    """
    type_string, reddit_id = fullname.split('_')
    current_posts = get_replied_entries(session)
    if reddit_id in current_posts:
        raise ValueError("Post reddit_id is already in replied posts list. This should never happen. The application may have double posted.")
    else:
        session.execute("INSERT INTO replied_entries (reddit_id, reply_succeeded_bool) VALUES (?, ?)", [reddit_id, int(reply_succeeded)])
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

def create_database(db_str: str):
    """
    Takes a file path and creates a database at that location if the file does not already exist.
    Raises an exception if the file specified exists and is not a sqlite3 database.
    Raises an exception if the file specified exists and does not match the expected schema.
    :param path: str denoting the file path. 
    """

    if os.path.isfile(db_str):
        #confirm file is a sqlite3 database:
        if os.path.getsize(db_str) < 100:
            raise sqlite3.OperationalError(f"File {db_str} is not a valid sqlite3 file.")
        with open(db_str, 'rb') as fd:
            header = fd.read(100)
            if not header[:16] == b'SQLite format 3\x00':
                raise sqlite3.OperationalError(f"File {db_str} is not a valid sqlite3 file.")

        try: #confirm we can connect to it as a rw sqlite3 database
            dburi = 'file:{}?mode=rw'.format(pathname2url(db_str))
            conn = sqlite3.connect(dburi, uri=True)
            cur = conn.cursor()

            # check that all 3 tables are present and match the expected schemas.
            #TODO: There's probably a more flexible/maintainable way to do this.
            cur.execute("PRAGMA table_info('books')")
            books = cur.fetchall()
            expected_book_columns = [(0, 'id', 'integer', 0, None, 1),
                                    (1, 'title', 'TEXT', 1, None, 0),
                                    (2, 'author', 'text', 1, None, 0),
                                    (3, 'isbn', 'text', 1, None, 0),
                                    (4, 'uri', 'text', 0, None, 0),
                                    (5, 'summary', 'text', 1, None, 0)]
            cur.execute("PRAGMA table_info('opted_in_users')")
            oiu = cur.fetchall()
            expected_opted_in_users = [(0, 'id', 'integer', 0, None, 1),
                                    (1, 'reddit_username', 'TEXT', 1, None, 0)]
            cur.execute("PRAGMA table_info('replied_entries')")
            re = cur.fetchall()
            expected_replied_entries = [(0, 'id', 'integer', 0, None, 1),
                                        (1, 'reddit_id', 'TEXT', 1, None, 0),
                                        (2, 'reply_succeeded_bool', 'integer', 1, None, 0)]
            
            #TODO: Is this an appropriate use of ProgrammingError?
            if not expected_book_columns == books:
                raise sqlite3.ProgrammingError("Table 'books' does note match the expected schema.")
            if not expected_opted_in_users == oiu:
                raise sqlite3.ProgrammingError("Table 'opted_in_users' does not match the expected schema.")
            if not expected_replied_entries == re:
                raise sqlite3.ProgrammingError("Table 'replied_entries' does not match the expected schema.")

            return #if it already exists and matches the schema, silently do nothing.

        except Exception as exception:
            raise exception
    else: 
        # create the database.
        conn = sqlite3.connect(db_str)
        cur = conn.cursor()
        cur.execute('CREATE TABLE books(id integer PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, author text NOT NULL, isbn text NOT NULL, uri text, summary text not null);')
        cur.execute('CREATE TABLE replied_entries (id integer PRIMARY KEY AUTOINCREMENT, reddit_id TEXT NOT NULL, reply_succeeded_bool integer NOT NULL);')
        cur.execute('CREATE TABLE opted_in_users (id integer PRIMARY KEY AUTOINCREMENT, reddit_username TEXT NOT NULL);')
        conn.commit()