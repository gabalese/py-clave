import os
from data import database, conn


def updateDB(db=database, ext="epub"):
    """

    :param db:
    :param ext:
    """
    for path, dirs, files in os.walk("."):
        for singular in files:
            if singular.endswith(ext):
                print os.path.join(path, singular)
                #  this is an EXPENSIVE function, use at startup
                #  update the DB, yada yada
