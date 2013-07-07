import sqlite3
import os

DBNAME = "base.sql"
EPUB_FILES_PATH = "."

if not os.path.exists(DBNAME):
    create = True
else:
    create = False

def opendb(name=DBNAME):
    """

    :param name:
    :return:
    """
    conn = sqlite3.connect(name)
    # noinspection PyPropertyAccess
    conn.row_factory = sqlite3.Row
    database = conn.cursor()
    return database, conn

if create:
    database, conn = opendb(DBNAME)
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
