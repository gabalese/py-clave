import zipfile as ZIP
import os
import re
import xml.etree.ElementTree as ET

from data.utils import opendb


NAMESPACE = {
    "dc": "{http://purl.org/dc/elements/1.1/}",
    "opf": "{http://www.idpf.org/2007/opf}",
    "ncx": "{http://www.daisy.org/z3986/2005/ncx/}"
}


class InvalidEpub(Exception):
    pass


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


#  #################
#  Utility functions,
#  TODO: REFACTOR
#  #################


class NCX(object):  # function to build an empty NCX tree
    def __init__(self):
        ncx = ET.Element("ncx")
        ncx.set("xmlns", "http://www.daisy.org/z3986/2005/ncx/")
        ncx.set("version", "2005-1")

        head = ET.SubElement(ncx, "head")
        docTitle = ET.SubElement(ncx, "docTitle")
        docTitleText = ET.SubElement(docTitle, "text")
        navMap = ET.SubElement(ncx, "navMap")
        ncx_tree = ET.ElementTree(ncx)


def buildNavPoint():  # builds a navpoint
    navPoint = ET.Element("navPoint")
    navLabel = ET.SubElement(navPoint, "navLabel")
    navLabelText = ET.SubElement(navLabel, "text")
    content = ET.SubElement(navPoint, "content")

    return navPoint
