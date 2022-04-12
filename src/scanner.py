import praw

r = praw.Reddit("bot1")
subreddit = r.subreddit("lightweaver_bot")

for submission in subreddit.hot(limit=5):
    print("Title: ", submission.title)
    print("Text: ", submission.selftext)
    print("Score: ", submission.score)
    print("---------------------------------\n")