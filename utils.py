import zipfile as ZIP
import sys
import os
import glob

try:
    from lxml import etree as ET
except ImportError:
    print("ERROR: lxml library must be installed.")
    # TODO: fallback for xml.Etree
    sys.exit(1)

namespaces = {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/"}


def listEpubFiles(ext):
    meta = []
    for i in glob.glob("*.%s" % ext):
        meta.append(EPUB(i).__dict__)
        # ouch. there must be a more elegant way
    return meta


class EPUB:
    def __init__(self, file):
        self.file = file
        opf = self.parseOPF(file)
        # this list must grow...
        self.title = opf.xpath("//dc:title/text()", namespaces=namespaces) or None
        self.author = opf.xpath("//dc:creator/text()", namespaces=namespaces) or None
        self.isbn = opf.xpath("//dc:identifier/text()", namespaces=namespaces) or None
        self.language = opf.xpath("//dc:language/text()", namespaces=namespaces) or None
        self.publisher = opf.xpath("//dc:publisher/text()", namespaces=namespaces) or None
        self.pubdate = opf.xpath("//dc:date[@opf:event='publication']/text()", namespaces=namespaces) or None

    def parseInfo(self, file):
        """
        Find where OPF and NCX files are in the epub archive
        :param file: file path
        :return: dict{"path_to_opf":path,"path_to_ncx":path}
        """
        info = {}
        try:
            f = ZIP.ZipFile(file).read("META-INF/container.xml")
        except KeyError:
            print
            "The %s file is not a valid OCF." % str(file)
        try:
            f = ET.fromstring(f)
            info["path_to_opf"] = f[0][0].get("full-path")
            root_folder = os.path.dirname(info["path_to_opf"])
        except:
            pass
        opf = ET.fromstring(ZIP.ZipFile(file).read(info["path_to_opf"]))

        id = opf.xpath("//opf:spine", namespaces=namespaces)[0].get("toc")
        expr = "//*[@id='{0:s}']".format(id)
        info["ncx_name"] = opf.xpath(expr)[0].get("href")
        info["path_to_ncx"] = root_folder + "/" + info["ncx_name"]
        info.pop("ncx_name")

        return info

    def parseOPF(self, file):
        """
        Parse a OPF content file
        :param file: file path
        :return: opf Element
        """
        opf = ET.fromstring(ZIP.ZipFile(file).read(self.parseInfo(file)["path_to_opf"]))
        return opf

    def parseNCX(self, file):

        """
        Parse a NCX index
        :param file: file path
        :return: ncx Element
        """
        ncx = ET.fromstring(ZIP.ZipFile(file).read(self.parseInfo(file)["path_to_ncx"]))

        return ncx

    def showToc(self):

        opf = ET.fromstring(ZIP.ZipFile(self.file).read(self.parseInfo(self.file)["path_to_opf"]))
        ret = []
        for i in opf[2]:
            ret.append(
                {"idref":i.get("idref"),"href":opf[1].xpath("//*[@id='%s']" % i.get("idref"))[0].get("href")}
            )
        return ret