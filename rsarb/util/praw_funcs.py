import praw, prawcore # type: ignore

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

def get_submission(praw_instance, fullname=None, URI=None):
    """
    Takes a praw instance and either a submission fullname or URI. 
    Retrieves and returns the submission.
    :param praw_instance: An instance of a praw.Reddit object.
    :param fullname: the fullname of a submission (e.g. t3_abcdef)
    :param uri: the full URI/permalink of a reddit thread. (e.g. https://www.reddit.com/r/<subreddit>/comments/<threadID/<threadtitle>
    :returns: A praw Submission, or None if none found.
    """

    if URI is None and fullname is None:
        raise Exception("Must specify either a fullname or URI.")
    if URI is not None:
        submission = praw_instance.submission(url=URI)
    else:
        name = fullname.split("_")[1]
        submission = praw_instance.submission(name=name)

    return submission

def get_comments(submission):
    """
    Iterates the comments in a given submission and returns a 
    list of comments as Reddit.comment objects.
    
    :returns: A list of reddit comment objects as list(Reddit.comment).
    """
    comments = []
    comment_forest = submission.comments
    for comment in comment_forest:
        comments.append(comment)
    return comments

def get_thread_commenters(submission):
    """
    Iterates the comments of the submission and collects the authors into a list. Deduplicates them and returns them.
    :param submission: Reddit.submission object.
    :returns: list[usernames: str]
    """
    comment_forest = get_comments(submission)
    authors = []
    for comment in comment_forest:
        authors.append(comment.author)
    authors = list({str(author).lower() for author in authors})
    return authors

def scan_entity(entity, books, replied_entries, opted_in_users):
    """
    Scans a given entity (submission, comment) and detects book titles by name
    scans the title of submissions, and the body of submissions and comments
    returns a list of books to reply to a given entity with.
    :param entity: A reddit comment or submission.
    :returns: list[book1, book2, book3, ...]
    :raises ValueError: If entity is not a valid comment or submission.
    """
    type_string, reddit_id = entity.fullname.split('_')
    if type_string not in ['t1','t3']:
        raise ValueError("Entity submitted is not a valid submission or comment.")

    if reddit_id in replied_entries:
        return []

    if entity.author not in opted_in_users:
        return []

    found_books = []
    for book in books:

        #submission
        if type_string == 't3':
            if book in entity.title.lower() or book in entity.selftext.lower():
                found_books.append(book)

        #comment
        if type_string == 't1':
            if book in entity.body.lower():
                found_books.append(book)

    found_books = list({str(book).lower() for book in found_books}) #de-duplicate list.

    return found_books

def post_comment(reddit, entity, post_body: str) -> bool:
    """
    Accepts an entity to reply to and a list of books to post information for.
    Posts the book information in a formatted block as a reply to the provided entity.
    :param entity: the Reddit object to reply to (submission or comment)
    :param books: a list of books as list[str]
    :returns: True if comment successfully posted, otherwise False.
    :raises: Exception when post does not submit to reddit properly.
    """
    try:
        result = entity.reply(post_body)
    except prawcore.exceptions.Forbidden as prawForbidden:
        #Replying to a locked or otherwise non-repliable post.
        return False

    if result is None:
        # posting to a non-opted in, quarantined sub
        last_posted_comment = reddit.user.me().comments.new(limit=1)[0] # get most recent comment
        if last_posted_comment.parent_id != entity.fullname: #check if the parent of most recent comment is the post just replied to
            return False
        else:
            return True

    return True

def get_user_replied_entities(reddit) -> list:
    """
    Takes a praw.Reddit instance.
    Returns a list of reddit entity fullnames e.g ['t3_abcdef', 't1_ghijkl', ...].
    This list is composed of all of the comments and submissions that this bot has successfully replied to.
    :param reddit: a praw.Reddit instance.
    :returns: list(str) of reddit base36 comment unique identifiers.
    """

    replied_entities = []
    own_comments = reddit.user.me().comments
    for comment in own_comments:
        replied_entities.append(comment.parent)
    
    replied_entities = list({str(entity.id).lower() for entity in replied_entities})
    return replied_entities