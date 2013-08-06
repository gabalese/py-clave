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


class EPUB(ZIP.ZipFile):
    def __init__(self, filename, mode="r"):
        if mode == "w":
            ZIP.ZipFile.__init__(self, filename, "w", )
            #  Add empty OPF [metadata, manifest, spine, guide]
            #  and relevant methods.
            pass
        else:
            self.__init__read(filename)

    def __init__read(self, filename):
        ZIP.ZipFile.__init__(self, filename, "r", )
        self.file = filename
        self.info = self.parseInfo(filename)
        self.meta = {}
        self.contents = []
        self.manifest = []
        ns = re.compile(r'\{.*?\}')
        meta_tree = self.opf.find("{0}metadata".format(NAMESPACE["opf"]))
        for i in meta_tree:
            i.tag = ns.sub('', i.tag)
            if i.tag not in self.meta:
                self.meta[i.tag] = i.text or i.attrib
            else:
                self.meta[i.tag] = [self.meta[i.tag], i.text or i.attrib]
        meta2 = self.opf.find('.//*[@name="cover"]')
        try:
            coverid = meta2.get("content")
        except AttributeError:
            coverid = None
        self.cover = coverid
        self.manifest = [{"id": x.get("id"), "href": x.get("href"), "mimetype": x.get("media-type")}
                         for x in self.opf.find("{0}manifest".format(NAMESPACE["opf"]))]
        self.id = self.opf.find('.//*[@id="{0}"]'.format(self.opf.get("unique-identifier"))).text
        ncx = self.parseNCX()
        self.contents = [{"name": i[0][0].text or "None",
                          "src": os.path.dirname(self.info["path_to_opf"]) + "/" + i[1].get("src"),
                          "id":i.get("id")}
                         for i in ncx.iter("{0}navPoint".format(NAMESPACE["ncx"]))]

    def parseInfo(self, filename):
        """
        Find where OPF and NCX files are in the epub archive
        :param filename: file path
        :return: dict{"path_to_opf":path,"path_to_ncx":path}
        """
        info = {}
        try:
            f = self.read("META-INF/container.xml")
        except KeyError:
            print "The %s file is not a valid OCF." % str(filename)
            raise InvalidEpub
        f = ET.fromstring(f)
        info["path_to_opf"] = f[0][0].get("full-path")
        root_folder = os.path.dirname(info["path_to_opf"])

        self.opf = self.parseOPF(info["path_to_opf"])

        toc_id = self.opf[2].get("toc")
        expr = ".//*[@id='{0:s}']".format(toc_id)
        try:
            info["ncx_name"] = self.opf.find(expr).get("href")
            info["path_to_ncx"] = root_folder + "/" + info["ncx_name"]
        except Exception:
            raise InvalidEpub

        return info

    def parseOPF(self, filename):
        """
        Parse a OPF content file
        :param filename: file path
        :return: opf Element
        """
        try:
            opf = ET.fromstring(self.read(filename))
        except Exception:
            raise InvalidEpub
        return opf

    def parseNCX(self):

        """
        Parse a NCX index
        :return: ncx Element
        """
        try:
            ncx = ET.fromstring(self.read(self.info["path_to_ncx"]))
        except Exception:
            raise InvalidEpub

        return ncx

    def add_meta(self, **kwargs):
        """

        :param kwargs:
        """
        pass

    def add_element(self, element):
        """
        Add an element to OPF
        :param element: xml.etree.Element
        """
        pass

    def add_content(self, filename, mimetype, elementid):
        """
        Add relevant content to EPUB archive
        :param filename: File (path) to be written into epub
        :param mimetype: mimetype
        :param elementid: id
        """
        pass


#  #################
#  Utility functions,
#  TODO: REFACTOR
#  #################


def buildNcx():  # function to build an empty NCX tree
    ncx = ET.Element("ncx")
    ncx.set("xmlns", "http://www.daisy.org/z3986/2005/ncx/")
    ncx.set("version", "2005-1")

    head = ET.SubElement(ncx, "head")
    docTitle = ET.SubElement(ncx, "docTitle")
    docTitleText = ET.SubElement(docTitle, "text")
    navMap = ET.SubElement(ncx, "navMap")
    ncx_tree = ET.ElementTree(ncx)

    return ncx_tree


def buildNavPoint():  # builds a navpoint
    navPoint = ET.Element("navPoint")
    navLabel = ET.SubElement(navPoint, "navLabel")
    navLabelText = ET.SubElement(navLabel, "text")
    content = ET.SubElement(navPoint, "content")

    return navPoint
