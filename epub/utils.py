import os
from data.utils import opendb


def listFiles():
    """

    :return:
    """
    meta = []
    database, conn = opendb()
    result = database.execute("""
                SELECT isbn, title, path, author FROM books ORDER BY title ASC
            """)
    for entry in result:
        meta.append({"id": entry["isbn"],
                     "title": entry["title"],
                     "filename": os.path.basename(entry["path"]),
                     "author": entry["author"]})
    return meta
