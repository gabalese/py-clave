import os
from data.utils import opendb
from collections import OrderedDict


def listFiles():
    """

    :return:
    """
    meta = OrderedDict()
    database, conn = opendb()
    result = database.execute("""
                SELECT isbn, title, path, author FROM books ORDER BY title ASC
            """)
    for entry in result:
        meta[entry["isbn"]] = {"title": entry["title"],
                               "filename": os.path.basename(entry["path"]),
                               "author": entry["author"]}
    return meta
