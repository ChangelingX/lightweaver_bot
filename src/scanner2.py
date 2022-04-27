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

    def scan_entry(self, entity: object) -> dict:
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
        comments_to_post[submission] = rs.scan_entry(submission)
        print(submission, comments_to_post[submission])
        for comment in comments[submission]:
            comments_to_post[comment] = rs.scan_entry(comment)
            print(comment, comments_to_post[comment])
    print(comments_to_post)

if __name__ == '__main__':
    main()