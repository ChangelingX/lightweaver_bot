from reddit_scan_and_reply_bot.RedditScanAndReplyBot import RedditScanAndReplyBot
import argparse
import os

def main(config):
    if config is None:
        raise Exception("No configuration file specified.")
    if not os.path.isfile(config):
        raise FileNotFoundError(f"Config file {config} not found.")
    rb = RedditScanAndReplyBot().from_file(config)
    rb.setup()
    rb.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scrapes reddit for hits on given keywords and posts relevant information as a reply.")
    parser.add_argument('--config', '-c', dest='config', required=True, metavar="./config_file.ini")
    args = parser.parse_args()
    main(args.config)