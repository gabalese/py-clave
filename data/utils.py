import os
import sqlite3
import time

from multiprocessing import Process, Queue

from data import DBNAME, EPUB_FILES_PATH
from epub import EPUB, InvalidEpub


def initdb():
    if not os.path.exists(DBNAME):
        print "No suitable DB found, creating one..."
        conn = sqlite3.connect(DBNAME)
        # noinspection PyPropertyAccess
        conn.row_factory = sqlite3.Row
        database = conn.cursor()
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
    else:
        return


def opendb(name=DBNAME):
    """

    :param name:
    :return:
    """
    initdb()
    conn = sqlite3.connect(name)
    # noinspection PyPropertyAccess
    conn.row_factory = sqlite3.Row
    database = conn.cursor()
    return database, conn


def insert_path_indb(queue):
    database, conn = opendb(DBNAME)
    # noinspection PyPropertyAccess
    conn.text_factory = str
    for path in queue:
        try:
            epubfile = EPUB(path)
        except InvalidEpub:
            print "INVALID! {}".format(path)
            continue
        except Exception, e:
            print e
            print "INVALID! {}".format(path)
            continue

        inserting_tuple = (unicode(epubfile.info["metadata"].get("creator")), unicode(epubfile.info["metadata"].get("title")),
                           epubfile.id, path, time.strftime("%Y-%m-%dT%H:%M:%S"))
        database.execute("INSERT OR REPLACE INTO books (author, title, isbn, path, timest) VALUES ( ?, ?, ?, ?, ? )",
                         inserting_tuple)
        conn.commit()


def delete_path_indb(queue):
    database, conn = opendb(DBNAME)
    # noinspection PyPropertyAccess
    conn.text_factory = str
    for path in queue:
        database.execute("DELETE FROM books WHERE path = ?", (path,))
        conn.commit()


def updateDB(ext="epub"):
    print "Begin database update at {}...".format(time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    start_time = time.time()
    database, conn = opendb(DBNAME)

    path_queue = Queue()  # path to insert
    remove_path_queue = Queue()  # path to remove

    dblist = database.execute("SELECT path FROM BOOKS").fetchall()
    dblist = [str(x[0]) for x in dblist]  # normalize

    walkerlist = []

    found = 0
    for path, dirs, files in os.walk(EPUB_FILES_PATH):
        for singular in files:
            if singular.endswith(ext):
                found += 1
                filepath = os.path.abspath(os.path.join(path, singular))
                walkerlist.append(filepath)

    # Analyze

    newfiles = set(walkerlist) - set(dblist)
    oldfiles = set(dblist) - set(walkerlist)

    for i in newfiles:
        path_queue.put(i)

    for i in oldfiles:
        remove_path_queue.put(i)

    WORKERS = 4
    insert_processes = []
    for i in xrange(WORKERS):
        p = Process(target=insert_path_indb, args=(iter(path_queue.get, None),))
        path_queue.put(None)
        p.start()
        insert_processes.append(p)

    for p in insert_processes:
        p.join()

    remove_processes = []
    for i in xrange(WORKERS):
        p = Process(target=delete_path_indb, args=(iter(remove_path_queue.get, None),))
        remove_path_queue.put(None)
        p.start()
        remove_processes.append(p)

    for p in remove_processes:
        p.join()

    x = database.execute(r"SELECT Count(*) FROM books").fetchone()
    print "FOUND: ", found
    print "NEW: ", len(newfiles)
    print "OLD: ", len(oldfiles)
    print "IN DATABASE: ", x[0]

    if found == x[0]:
        print "OK"
    else:
        print "Something went wrong!"

    conn.close()
    print "Update done in {} seconds".format(round((time.time()-start_time), 2))


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
