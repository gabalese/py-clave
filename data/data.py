import sqlite3
import os

DBNAME = "base.sql"

create = False
if not os.path.exists(DBNAME):
    create = True


def opendb(name):
    conn = sqlite3.connect(DBNAME)
    conn.row_factory = sqlite3.Row
    database = conn.cursor()
    return database, conn

if create:
    database, conn = opendb(DBNAME)#  insert dummy data in DB
    database.execute("""
        CREATE TABLE IF NOT EXISTS books(author text, title text, isbn text, path text);
    """)

    database.execute("""
    INSERT INTO books VALUES ("Giulio Cesare", "De Bello Gallico", "97888", "./here")
    """)
    conn.commit()
    conn.close()
