import os
import time

from multiprocessing import Process, Queue, current_process

from data import DBNAME, opendb, EPUB_FILES_PATH
import epub.utils


def insert_path_indb(queue, database, conn):
    while True:
        path = queue.get()
        print "{} GOT {}".format(current_process(), path)
        try:
            epubfile = epub.utils.EPUB(path)
        except epub.utils.InvalidEpub:
            pass
        inserting_tuple = (unicode(epubfile.meta.get("creator")), unicode(epubfile.meta.get("title")),
                           epubfile.id, path, time.strftime("%Y-%m-%dT%H:%M:%S"))
        database.execute("INSERT OR REPLACE INTO books (author, title, isbn, path, timest) VALUES ( ?, ?, ?, ?, ? )",
                         inserting_tuple)
        conn.commit()


def updateDB(db=DBNAME, ext="epub"):
    print "Updating database..."
    start_time = time.time()
    database, conn = opendb(db)
    conn.text_factory = str

    path_queue = Queue()
    
    WORKERS = 2
    for path, dirs, files in os.walk(EPUB_FILES_PATH):
        for singular in files:
            if singular.endswith(ext):
                filepath = os.path.join(path, singular)
                path_queue.put(filepath)
                print filepath

    processes = []
    for i in xrange(WORKERS):
        p = Process(target=insert_path_indb, args=(path_queue, database, conn))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    conn.close()
    print "Update done in {}".format((time.time()-start_time)*1000.00)
