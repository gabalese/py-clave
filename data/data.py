import sqlite3
import os


DBNAME = "base.sql"

create = False
if not os.path.exists(DBNAME):
    create = True


def opendb(name=DBNAME):
    conn = sqlite3.connect(name)
    # noinspection PyPropertyAccess
    conn.row_factory = sqlite3.Row
    database = conn.cursor()
    return database, conn

if create:
    database, conn = opendb(DBNAME)  # insert dummy data in DB
    database.execute("""
        CREATE TABLE IF NOT EXISTS
            books(
                author text,
                title text,
                isbn text UNIQUE,
                path text PRIMARY KEY
                );
    """)
    conn.commit()
    conn.close()
