from xml.etree import ElementTree as ET
import utils
from epub import EPUB
from etbuilder import Builder
import uuid
import time
import os


E = Builder()


def generateCatalogRoot():
    feed = E("feed",
             E("id", "urn:uuid:"+str(uuid.uuid1())),
             E("link", rel="self", href="/opds-catalog",
               type="application/atom+xml;profile=opds-catalog;kind=navigation"),
             E("link", rel="start", href="/opds-catalog",
               type="application/atom+xml;profile=opds-catalog;kind=navigation"),
             E("title", "py-clave Catalogue"),
             E("updated", "{0}".format(time.strftime("%Y-%m-%dT%H:%M:%SZ"))),
             E("author",
               E("name", "py-clave"),
               E("uri", "/")
               ),
             xmlns="http://www.w3.org/2005/Atom"
             )
    database, conn = utils.opendb()
    result = database.execute("""
                SELECT author, isbn, title, path, timest FROM books ORDER BY timest DESC
            """)
    for item in result:
        epub = EPUB(item["path"])
        entry = ET.SubElement(feed, "entry")
        entry_title = ET.SubElement(entry, "title")
        entry_title.text = item["title"]
        entry_id = ET.SubElement(entry, "id")
        entry_id.text = item["isbn"]
        entry_updated = ET.SubElement(entry, "updated")
        entry_updated.text = item["timest"]
        entry_author = ET.SubElement(entry, "author")
        entry_author_name = ET.SubElement(entry_author, "name")
        entry_author_name.text = item["author"]
        entry_author_uri = ET.SubElement(entry_author, "uri")
        entry_author_uri.text = ""
        entry_language = ET.SubElement(entry, "{http://purl.org/dc/terms}language")
        entry_language.text = epub.info["metadata"].get("language", "")
        entry_issued = ET.SubElement(entry, "{http://purl.org/dc/terms}issued")
        try:
            entry_issued.text = epub.info["metadata"]["date"][0]
        except KeyError:
            entry_issued.text = item["timest"]
        entry_summary = ET.SubElement(entry, "summary")
        entry_summary.text = epub.info["metadata"].get("description", "")
        ET.SubElement(entry, "link", rel="http://opds-spec.org/acquisition",
                      href="/book/{0}/download".format(item["isbn"]), type="application/epub+zip")
        ET.SubElement(entry, "link", rel="http://opds-spec.org/image",
                      href="/book/{0}/manifest/{1}".format(item["isbn"], epub.cover), type="image/jpg")
        ET.SubElement(entry, "link", rel="http://opds-spec.org/image/thumbnail",
                      href="/book/{0}/manifest/{1}".format(item["isbn"], epub.cover), type="image/jpg")

    output = ET.tostring(feed, encoding="UTF-8")
    return output


def generateAcquisitionFeed():
    pass  # TODO: implement


def updateCatalog():
    catalogue = generateCatalogRoot()
    with open(os.path.join(os.path.dirname(__file__), os.path.pardir, "feed.xml"), "w") as f:
        f.write(catalogue)
    print "Catalogue updated at {}".format(time.strftime("%Y-%m-%dT%H:%M:%SZ"))
