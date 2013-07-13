from xml.etree import ElementTree as ET
from data import opendb
from epub.utils import EPUB
from etbuilder import Builder
import uuid
import StringIO
import time


E = Builder()


def generateCatalogRoot():
    feed = E("feed",
             E("id", "urn:uuid:"+str(uuid.uuid1())),
             E("link", rel="self", href="/opds-catalog",
               type="application/atom+xml;profile=opds-catalog;kind=navigation"),
             E("link", rel="start", href="/opds-catalog",
               type="application/atom+xml;profile=opds-catalog;kind=navigation"),
             E("title", "OPDS Catalog Root"),
             E("updated", "{0}".format(time.strftime("%Y-%m-%dT%H:%M:%SZ"))),
             E("author",
               E("name", "py-clave"),
               E("uri", "/")
               ),
             xmlns="http://www.w3.org/2005/Atom"
             )
    database, conn = opendb()
    result = database.execute("""
                SELECT author, isbn, title, path, timest FROM books
            """)
    for item in result:
        epub = EPUB(item["path"])
        entry = ET.SubElement(feed, "entry")
        entry_title = ET.SubElement(entry, "title")
        entry_title.text = item["title"]
        entry_id = ET.SubElement(entry, "id")
        entry_id.text = item["isbn"]
        entry_updated = ET.SubElement(entry, "updated")
        entry_updated.text = time.strftime("%Y-%m-%dT%H:%M:%S")
        entry_author = ET.SubElement(entry, "author")
        entry_author_name = ET.SubElement(entry_author, "name")
        entry_author_name.text = item["author"]
        entry_author_uri = ET.SubElement(entry_author, "uri")
        entry_author_uri.text = ""
        entry_language = ET.SubElement(entry, "{http://purl.org/dc/terms}language")
        entry_language.text = epub.meta["language"] or ""
        entry_issued = ET.SubElement(entry, "{http://purl.org/dc/terms}issued")
        try:
            entry_issued.text = epub.meta["date"][0]
        except KeyError:
            entry_issued.text = ""
        entry_summary = ET.SubElement(entry, "summary")
        try:
            entry_summary.text = epub.meta["description"]
        except KeyError:
            pass
        link = ET.SubElement(entry, "link", rel="http://opds-spec.org/acquisition",
                             href="/book/{0}/download".format(item["isbn"]), type="application/epub+zip")
    output = StringIO.StringIO()
    ET.ElementTree(feed).write(output, encoding="UTF-8", xml_declaration=True)
    return output.getvalue()


def generateAcquisitionFeed():
    pass  # TODO: implement
