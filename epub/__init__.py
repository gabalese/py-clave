import zipfile as ZIP
import os
import re
import uuid
import xml.etree.ElementTree as ET


NAMESPACE = {
    "dc": "{http://purl.org/dc/elements/1.1/}",
    "opf": "{http://www.idpf.org/2007/opf}",
    "ncx": "{http://www.daisy.org/z3986/2005/ncx/}"
}


class InvalidEpub(Exception):
    pass


class EPUB(ZIP.ZipFile):
    """
    EPUB file representation. Rewrite of EPUB.py 0.51 by exirel

    """
    def __init__(self, filename, mode="r"):
        """
        Global Init Switch
        """
        if mode == "w":
            ZIP.ZipFile.__init__(self, filename, mode="w")
            self.__init__write(filename)
        else:  # retrocompatibility?
            ZIP.ZipFile.__init__(self, filename, mode="r")
            self.__init__read(filename)
        pass

    def __init__read(self, filename):
        """
        Init if read file
        """
        try:
            # Read the container
            f = self.read("META-INF/container.xml")
        except KeyError:
            # By specification, there MUST be a container.xml in EPUB
            print "The %s file is not a valid OCF." % str(filename)
            raise InvalidEpub
        try:
            # There MUST be a full path attribute on first grandchild...
            opf_path = ET.fromstring(f)[0][0].get("full-path")
        except IndexError:
            #  ...else the file is invalid.
            print "The %s file is not a valid OCF." % str(filename)
            raise InvalidEpub

        # NEW: json-able info tree
        self.info = {"metadata": {},
                     "manifest": [],
                     "spine": [],
                     "guide": []}

        self.root_folder = os.path.dirname(opf_path)   # Used to compose absolute paths for reading in zip archive
        self.opf = ET.fromstring(self.read(opf_path))  # OPF tree

        ns = re.compile(r'\{.*?\}')  # RE to strip {namespace} mess

        # Iterate over <metadata> section, fill EPUB.info["metadata"] dictionary
        for i in self.opf.find("{0}metadata".format(NAMESPACE["opf"])):
            i.tag = ns.sub('', i.tag)
            if i.tag not in self.info["metadata"]:
                self.info["metadata"][i.tag] = i.text or i.attrib
            else:
                self.info["metadata"][i.tag] = [self.info["metadata"][i.tag], i.text or i.attrib]

        # Get id of the cover in <meta name="cover" />
        try:
            coverid = self.opf.find('.//*[@name="cover"]').get("content")
        except AttributeError:
            # It's a facultative field, after all
            coverid = None

        # This is the manifest ID of the cover
        # Decide if you want the path
        self.cover = coverid

        self.info["manifest"] = [{"id": x.get("id"),
                                  "href": x.get("href"),
                                  "mimetype": x.get("media-type")}
                                 for x in self.opf.find("{0}manifest".format(NAMESPACE["opf"]))]

        self.info["spine"] = [{"idref": x.get("idref")} for x in self.opf.find("{0}spine".format(NAMESPACE["opf"]))]
        self.info["guide"] = [{"href": x.get("href"),
                               "type": x.get("type"),
                               "title": x.get("title")}
                              for x in self.opf.find("{0}guide".format(NAMESPACE["opf"]))]

        # Universal identifier
        self.id = self.opf.find('.//*[@id="{0}"]'.format(self.opf.get("unique-identifier"))).text

        # Get and parse the TOC
        toc_id = self.opf[2].get("toc")
        expr = ".//*[@id='{0:s}']".format(toc_id)
        toc_name = self.opf.find(expr).get("href")
        toc_path = self.root_folder + "/" + toc_name

        ncx = ET.fromstring(self.read(toc_path))
        self.contents = [{"name": i[0][0].text or "None",
                          "src": self.root_folder + "/" + i[1].get("src"),
                          "id":i.get("id")}
                         for i in ncx.iter("{0}navPoint".format(NAMESPACE["ncx"]))]

    def __init__write(self, filename):
        """
        Init for empty EPUB
        """
        self.writestr('mimetype', "application/epub+zip")
        self.opf_path = "OEBPS/content.opf"
        uid_id = 'BookId'
        self.uid = '%s' % uuid.uuid4()
        self.meta = {}
        self.contents = []
        self.manifest = []
        #  Do whatevah it takes...
        #  Then _read.
        self.__init__read(filename)
