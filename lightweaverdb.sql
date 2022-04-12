PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE books(id integer NOT NULL, title TEXT NOT NULL, author text NOT NULL, isbn text NOT NULL, uri text, summary text not null);
INSERT INTO books VALUES(1,'Opening the Hand of Thought','Kosho Uchiyama','9780861713578','https://wisdomexperience.org/product/opening-hand-thought/','For over thirty years, Opening the Hand of Thought has offered an introduction to Zen Buddhism and meditation unmatched in clarity and power. This is the revised edition of Kosho Uchiyama’s singularly incisive classic.');
COMMIT;
