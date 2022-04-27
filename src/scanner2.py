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
        :raises ValueError: If entity cannot be found or has already been replied to.
        """
        type_string, id = entity.fullname.split('_')
        print(type_string, id)
        if type_string == 't3':
            print("submission")
            print(entity.title, entity.selftext)
        if type_string == 't1':
            print("comment")

def main():
    rs = Reddit_Scanner()
    submissions = rs.get_submissions()
    comments = {}
    for submission in submissions:
        comments[submission] = rs.get_comments(submission)

     #At this point we have all of the submissions and their comments in the format 
     #dict[submission] = list[comments] 

    rs.scan_entry(submissions[0])
        

if __name__ == '__main__':
    main()