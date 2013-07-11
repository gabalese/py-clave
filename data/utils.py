import os
from data import DBNAME, opendb, EPUB_FILES_PATH
import epub.utils


def updateDB(db=DBNAME, ext="epub"):
    """

    :param db:
    :param ext:
    """
    print "Updating db %s..." % os.path.basename(db)
    database, conn = opendb(db)
    for path, dirs, files in os.walk(EPUB_FILES_PATH):
        for singular in files:
            try:
                if singular.endswith(ext):
                    filepath = os.path.join(path, singular)
                    epubfile = epub.utils.EPUB(filepath)
                    database.execute("""
                        INSERT OR REPLACE INTO books (author, title, isbn, path) VALUES ( '{0}', '{1}', '{2}', '{3}' )
                    """.format(epubfile.meta["creator"],
                               epubfile.meta["title"],
                               epubfile.id,
                               filepath))
            except Exception, e:
                print "error: {} - {}".format(singular, e)

    else:
        conn.commit()
        conn.close()
        print "... update done."

if __name__ == "__main__":
    updateDB()  # autotest only
