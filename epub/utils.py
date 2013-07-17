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
                SELECT isbn, title, path FROM books
            """)
    for entry in result:
        meta[entry["isbn"]] = [entry["title"], os.path.basename(entry["path"])]
    return meta


class EPUB(ZIP.ZipFile):
    def __init__(self, filename):
        try:
            ZIP.ZipFile.__init__(self, filename, "r", )
            self.file = filename
            opf = self.parseOPF(filename)
            self.meta = {}
            self.contents = []
            for i in opf.find("{0}metadata".format(NAMESPACE["opf"])):
                i.tag = re.sub('\{.*?\}', '', i.tag)
                if i.tag not in self.meta:
                    self.meta[i.tag] = i.text or i.attrib
                else:
                    self.meta[i.tag] = [self.meta[i.tag], i.text or i.attrib]
            self.id = opf.find('.//*[@id="{0}"]'.format(opf.get("unique-identifier"))).text

            ncx = self.parseNCX(filename)
            for i in ncx.iter("{0}navPoint".format(NAMESPACE["ncx"])):
                self.contents.append({i.get("id"): os.path.dirname(self.parseInfo(filename)["path_to_opf"]) + "/" + i[1].get("src")})
        except:
            raise InvalidEpub


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

        opf = ET.fromstring(self.read(info["path_to_opf"]))

        toc_id = opf[2].get("toc")
        expr = ".//*[@id='{0:s}']".format(toc_id)
        info["ncx_name"] = opf.find(expr).get("href")
        info["path_to_ncx"] = root_folder + "/" + info["ncx_name"]
        info.pop("ncx_name")

        return info

    def parseOPF(self, filename):
        """
        Parse a OPF content file
        :param filename: file path
        :return: opf Element
        """
        opf = ET.fromstring(self.read(self.parseInfo(filename)["path_to_opf"]))
        return opf

    def parseNCX(self, filename):

        """
        Parse a NCX index
        :param filename: file path
        :return: ncx Element
        """
        ncx = ET.fromstring(self.read(self.parseInfo(filename)["path_to_ncx"]))

        return ncx
