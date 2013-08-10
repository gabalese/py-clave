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
        meta[entry["isbn"]] = [entry["title"], os.path.basename(entry["path"]), entry["author"]]
    return meta
