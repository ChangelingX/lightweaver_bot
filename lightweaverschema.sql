CREATE TABLE books(id integer NOT NULL, title TEXT NOT NULL, author text NOT NULL, isbn text NOT NULL, uri text, summary text not null);
CREATE TABLE replied_entries (id integer NOT NULL, reddit_id TEXT NOT NULL);
CREATE TABLE opted_in_users (id integer NOT NULL, reddit_username TEXT NOT NULL);
