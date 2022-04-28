import praw
import sqlite3

class Reddit_Scanner:

    def __init__(self):
        self.r = praw.Reddit("bot1")
        self.subreddit = self.r.subreddit("lightweaver_bot")

        con = sqlite3.connect('lightweaver.db')
        cur = con.cursor()
        cur.execute('SELECT title FROM books')
        self.books = cur.fetchall()
        cur.execute('SELECT reddit_username FROM opted_in_users')
        self.opted_in_users = cur.fetchall()

    #TODO: get commentors on opt-in post.

    def get_submissions(self) -> list:
        """
        Iterates the submissions for assigned subreddits and returns a 
        list of submissions as Reddit.submission objects.

        :returns: list[Reddit.submission]
        """
        submissions = []
        for submission in self.subreddit.top("all"):
            submissions.append(submission)
        return submissions

    def get_comments(self, submission: object) -> list:
        """
        Iterates the comments in a given submission and returns a 
        list of comments as Reddit.comment objects.
        
        :returns: A dictionary of 
        :raises ValueError: If invalid submission is passed.
        """
        comments = []
        comment_forest = submission.comments
        for comment in comment_forest:
            comments.append(comment)
        return comments

    def scan_entity(self, entity: object) -> dict:
        """
        Scans a given entity (submission, comment) and detects book titles by name
        scans the title of submissions, and the body of submissions and comments
        returns a list of books to reply to a given entity with.

        :param entity: A reddit comment or submission.
        :returns: list[book1, book2, book3, ...]
        :raises ValueError: If entity is not a valid comment or submission.
        """
        
        type_string, id = entity.fullname.split('_')
        if type_string not in ['t1','t3']:
            raise ValueError("Entity submitted is not a valid submission or comment.")

        con = sqlite3.connect('lightweaver.db') #check if we have already replied to a given entity
        cur = con.cursor()
        cur.execute("SELECT reddit_id FROM replied_entries WHERE reddit_id = ?", [id])
        already_replied = cur.fetchone()
        if already_replied is not None:
            return None

        if entity.author == self.r.user.me(): #avoid replying to self
            return None

        if entity.author not in self.opted_in_users: #Reply only to users who have opted into this bot.
            return None
        
        found_books = []
        for book in self.books:
            book = str(book[0]).lower() #sqlite3 returns a tuple, converting to string.

            #submission
            if type_string == 't3':
                if book in entity.title.lower() or book in entity.selftext.lower():
                    found_books.append(book)

            #comment
            if type_string == 't1':
                if book in entity.body.lower():
                    found_books.append(book)

        found_books = list(dict.fromkeys(found_books)) #de-duplicate list
        return found_books


    def post_comment(self, entity: object, books: list) -> None:
        """
        Accepts an entity to reply to and a list of books to post information for.
        Posts the book information in a formatted block as a reply to the provided entity.

        :param entity: the Reddit object to reply to (submission or comment)
        :param books: a list of books as list[str]
        :returns: None
        :raises: Exception when post does not submit to reddit properly.

        """
        post_body = get_formatted_post_body(books)

        posted_reply = entity.reply(post_body)

        if posted_reply is None:
            raise Exception("Unknown error has occurred while attempting to post reply.")
        
        #Creates entry in database to track replied posts.
        con = sqlite3.connect('lightweaver.db')
        cur = con.cursor()
        cur.execute("SELECT MAX(id) FROM replied_entries")
        max_id = cur.fetchone()
        next_id = max_id[0] + 1
        cur.execute("INSERT INTO replied_entries (id, reddit_id) VALUES (?, ?)", [next_id, entity.id])
        con.commit()

def get_formatted_post_body(books: list) -> str:
    """
    Accepts a list of books by title, formats them into a complete post body for a text post.
    
    :param books: list[str]
    :returns: str
    """
    post_body = ""
    header = "Hello, I am Lightweaver_bot. I post information on books mentioned in the parent comment or submission.\n\n"

    for book in books:
        post_body = post_body + "--------------------------------\n\n" + get_book_db_entry(book)

    footer = "--------------------------------\n\n"+\
             "Please DM this bot, the author, or post on /r/lightweaver_bot with any feedback or suggestions.\n"+\
             "Author: /u/HoweveritHasToHappen\n\n"

    post_body = header + post_body + footer
    return post_body

def get_book_db_entry(title: str) -> str:
    """
    Accepts a title of a book. Returns the database entry for that book in a formatted block.
    
    :param title: str
    :returns: str
    :raises KeyError: If title is not found in database.
    """
    con = sqlite3.connect('lightweaver.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM books WHERE title =:title COLLATE NOCASE", {"title": title})
    book_db_entry = cur.fetchone()

    if book_db_entry is None:
        raise KeyError("Title not found in database.")

    book_db_entry = "Title:\t"+book_db_entry[1]+"\n\n"+\
                    "Author:\t"+book_db_entry[2]+"\n\n"+\
                    "ISBN:\t"+book_db_entry[3]+"\n\n"+\
                    "URI:\t"+book_db_entry[4]+"\n\n"#+\
                    #"Desc:\t"+book_db_entry[5]+"\n\n"
    return book_db_entry

def main():
    rs = Reddit_Scanner()
    submissions = rs.get_submissions()
    comments = {}
    for submission in submissions:
        comments[submission] = rs.get_comments(submission)

     #At this point we have all of the submissions and their comments in the format 
     #dict[submission] = list[comments] 

    comments_to_post = {}
    for submission in submissions:
        comments_to_post[submission] = rs.scan_entity(submission)
        print(submission, comments_to_post[submission])
        for comment in comments[submission]:
            comments_to_post[comment] = rs.scan_entity(comment)
            print(comment, comments_to_post[comment])
    for key in comments_to_post.keys():
        if comments_to_post[key] is None or len(comments_to_post[key]) == 0:
            continue
        print(f"Entity: {key}")
        print(f"Hits: {comments_to_post[key]}")
        rs.post_comment(key, comments_to_post[key])

if __name__ == '__main__':
    main()