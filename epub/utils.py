import os
from data.utils import opendb


def listFiles():
    """

    :return:
    """
    meta = {}
    database, conn = opendb()
    result = database.execute("""
                SELECT isbn, title, path, author FROM books
            """)
    for entry in result:
        meta[entry["isbn"]] = {"title": entry["title"],
                               "filename": os.path.basename(entry["path"]),
                               "author": entry["author"]}
    return meta
