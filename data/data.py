import sqlite3
import os

DBNAME = os.path.join(os.path.dirname(__file__), os.pardir, "base.sql")
EPUB_FILES_PATH = os.path.join(os.path.dirname(__file__), os.pardir, "files")

if not os.path.exists(DBNAME):
    create = True
else:
    create = False


class DatabaseConnection():
    def __init__(self, name=DBNAME):
        self.conn = sqlite3.connect(name)
        # noinspection PyPropertyAccess
        self.conn.row_factory = sqlite3.Row
        self.database = self.conn.cursor()

    def insert(self):
        pass

    def query(self, field, query):
        result = self.database.execute("SELECT * FROM books WHERE {} LIKE '%{}%'".format(field, query)).fetchall()
        return result

    def update(self):
        pass

    def exit(self):
        self.conn.commit()
        self.conn.close()


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
    print "No suitable DB found, creating one..."
    database, conn = opendb()
    database.execute("""
        CREATE TABLE IF NOT EXISTS
            books(
                author text,
                title text,
                isbn text UNIQUE,
                path text PRIMARY KEY,
                timest timestamp
                );
    """)
    conn.commit()
    conn.close()
    print "DB created, with the name of %s" % os.path.basename(DBNAME)
