import os
import time

from multiprocessing import Process, Queue

from data import DBNAME, opendb, EPUB_FILES_PATH
import epub.utils

insertions = 0


def insert_path_indb(queue):
    database, conn = opendb(DBNAME)
    conn.text_factory = str
    for path in queue:
        try:
            epubfile = epub.utils.EPUB(path)
        except epub.utils.InvalidEpub, e:
            print "INVALID! {}".format(path)
            continue
        except Exception, e:
            print e
            print "INVALID! {}".format(path)
            continue

        inserting_tuple = (unicode(epubfile.meta.get("creator")), unicode(epubfile.meta.get("title")),
                           epubfile.id, path, time.strftime("%Y-%m-%dT%H:%M:%S"))
        database.execute("INSERT OR REPLACE INTO books (author, title, isbn, path, timest) VALUES ( ?, ?, ?, ?, ? )",
                         inserting_tuple)
        global insertions
        insertions += 1
        conn.commit()


def updateDB(ext="epub"):
    print "Updating database..."
    start_time = time.time()
    path_queue = Queue()

    WORKERS = 4
    found = 0
    for path, dirs, files in os.walk(EPUB_FILES_PATH):
        for singular in files:
            if singular.endswith(ext):
                found += 1
                filepath = os.path.join(path, singular)
                path_queue.put(filepath)

    processes = []
    for i in xrange(WORKERS):
        p = Process(target=insert_path_indb, args=(iter(path_queue.get, None),))
        p.start()
        processes.append(p)
        path_queue.put(None)

    for p in processes:
        p.join()

    database, conn = opendb(DBNAME)
    x = database.execute(r"SELECT Count(*) FROM books").fetchone()
    print "FOUND ", found
    print "INSERTED ", x[0]
    print "INSERTIONS MADE ", insertions
    conn.close()
    print "Update done in {}".format((time.time()-start_time)*1000.00)
