import sqlite3
import os

create = False
if not os.path.exists("base.sql"):
    create = True

conn = sqlite3.connect("base.sql")
conn.row_factory = sqlite3.Row

database = conn.cursor()

if create:
    database.execute("""
        CREATE TABLE IF NOT EXISTS books(author text, title text, isbn text, path text);
    """)

    database.execute("""
    INSERT INTO books VALUES ("Giulio Cesare", "De Bello Gallico", "97888", "./here")
    """)
    conn.commit()
