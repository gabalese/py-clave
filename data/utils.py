import os
from data import DBNAME, opendb
import epub.utils


def updateDB(db=DBNAME, ext="epub"):

    print "Updating db %s..." % db
    database, conn = opendb(db)
    for path, dirs, files in os.walk("."):
        for singular in files:
            if singular.endswith(ext):
                filepath = os.path.join(path, singular)
                epubfile = epub.utils.EPUB(filepath)
                database.execute("""
                    INSERT OR REPLACE INTO books (author, title, isbn, path) VALUES ( '{0}', '{1}', '{2}', '{3}' )
                """.format(epubfile.meta["creator"],
                           epubfile.meta["title"],
                           epubfile.id,
                           filepath))
    else:
        conn.commit()
        conn.close()
        print "... update over."
        #  this is an EXPENSIVE function, use at startup

if __name__ == "__main__":
    updateDB(DBNAME)  # autotest only
