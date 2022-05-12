import praw # type: ignore

def connect_to_reddit(client_id, client_secret, password, username, user_agent):
    ph = praw.Reddit(
        client_id = client_id,
        client_secret = client_secret,
        password = password,
        username = username,
        user_agent = user_agent
    )
    return ph

def get_submissions(praw_instance, subreddits_to_scan: str):
    """
    Takes a praw instance and a list of subreddits to collect.
    Collects these subreddits latest submissions and gathers them into a list.
    :returns: praw.ListingGenerator[Submission] (really Any because praw has no stubs.)
    """
    submissions = praw_instance.subreddit(subreddits_to_scan).new()
    return submissions

def get_comments(submission):
    """
    Iterates the comments in a given submission and returns a 
    list of comments as Reddit.comment objects.
    
    :returns: A list of reddit comment objects as list(Reddit.comment).
    :raises ValueError: If invalid submission is passed.
    """
    comments = []
    comment_forest = submission.comments
    for comment in comment_forest:
        comments.append(comment)
    return comments