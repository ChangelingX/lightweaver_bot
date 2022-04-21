PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE books(id integer NOT NULL, title TEXT NOT NULL, author text NOT NULL, isbn text NOT NULL, uri text, summary text not null);
INSERT INTO books VALUES(1,'Opening the Hand of Thought','Kosho Uchiyama','9780861713578','https://wisdomexperience.org/product/opening-hand-thought/','For over thirty years, Opening the Hand of Thought has offered an introduction to Zen Buddhism and meditation unmatched in clarity and power. This is the revised edition of Kosho Uchiyama’s singularly incisive classic.');
INSERT INTO books VALUES(2,'You Are The One You''ve Been Waiting For','Richard C Schwartz','9780615249322','https://ifs-institute.com/store/37','In this book, Richard Schwartz, the developer of the Internal Family Systems Model, applies the IFS Model to the topic of intimate relationships in an engaging, understandable, and personal style. Therapists and lay people alike will find this book to be an insightful exploration of how cultivating a relationship with the Self—the wise center of clarity, calmness, and compassion in each of us—creates the foundation for courageous love and resilient intimacy: the capacity to sustain and nourish a healthy intimate relationship. Self-leadership also allows us to embrace our partner''s feedback and use it to discover aspects of ourselves that seek healing. The book includes user-friendly exercises to facilitate learning.');
CREATE TABLE replied_entries (id integer NOT NULL, reddit_id TEXT NOT NULL);
INSERT INTO replied_entries (id, reddit_id) VALUES (0,"dummy");
COMMIT;
