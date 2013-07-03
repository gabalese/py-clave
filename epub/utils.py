import zipfile as ZIP
import sys
import os
import glob
import re
import xml.etree.ElementTree as ET


NAMESPACE = {
    "dc": "{http://purl.org/dc/elements/1.1/}",
    "opf": "{http://www.idpf.org/2007/opf}"
}

def listEpubFiles(ext):
    """

    :param ext:
    :return:
    """
    meta = []
    for i in glob.glob("./files/*.%s" % ext):
        meta.append(EPUB(i).file)
        # TODO: search cache first, list files only if db less recent than X
    return meta


class EPUB:
    def __init__(self, file):
        self.file = file
        opf = self.parseOPF(file)
        self.meta = {}
        self.contents = []
        for i in opf.find("{0}metadata".format(NAMESPACE["opf"])):
            i.tag = re.sub('\{.*?\}', '', i.tag)
            self.meta[i.tag] = i.text or i.attrib
        for i in opf.find("{0}spine".format(NAMESPACE["opf"])):
            self.contents.append(os.path.dirname(self.parseInfo(file)["path_to_opf"]) + '/' + \
                                           opf.find(".//*[@id='%s']" % i.get("idref")).get("href"))


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
            print "The %s file is not a valid OCF." % str(file)
        f = ET.fromstring(f)
        info["path_to_opf"] = f[0][0].get("full-path")
        root_folder = os.path.dirname(info["path_to_opf"])

        opf = ET.fromstring(ZIP.ZipFile(file).read(info["path_to_opf"]))

        toc_id = opf[2].get("toc")
        expr = ".//*[@id='{0:s}']".format(toc_id)
        info["ncx_name"] = opf.find(expr).get("href")
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
