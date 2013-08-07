import zipfile as ZIP
import os
import re
import uuid
import StringIO

from xml.dom import minidom
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
            filename = StringIO.StringIO()
            ZIP.ZipFile.__init__(self, filename, mode="w")
            self.__init__write(filename)
        else:  # retrocompatibility?
            ZIP.ZipFile.__init__(self, filename, mode="r")
            self.__init__read(filename)

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
        self.cover = coverid

        self.info["manifest"] = [{"id": x.get("id"),
                                  "href": x.get("href"),
                                  "mimetype": x.get("media-type")}
                                 for x in self.opf.find("{0}manifest".format(NAMESPACE["opf"]))]

        self.info["spine"] = [{"idref": x.get("idref")} for x in self.opf.find("{0}spine".format(NAMESPACE["opf"]))]
        try:
            self.info["guide"] = [{"href": x.get("href"),
                                   "type": x.get("type"),
                                   "title": x.get("title")}
                                  for x in self.opf.find("{0}guide".format(NAMESPACE["opf"]))]
        except TypeError:
            self.info["guide"] = None

        # Document identifier
        try:
            self.id = self.opf.find('.//*[@id="{0}"]'.format(self.opf.get("unique-identifier"))).text
        except AttributeError:
            raise InvalidEpub

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
        self.opf_path = "OEBPS/content.opf"  # Define a default folder for contents
        self.root_folder = "OEBPS"
        self.uid = '%s' % uuid.uuid4()

        self.writestr('mimetype', "application/epub+zip")
        self.writestr('META-INF/container.xml', self._containerxml())
        self._init_opf()
        self.__init__read(filename)

    def _init_opf(self):
        doc = minidom.Document()
        package = doc.createElement('package')
        package.setAttribute('version', "2.0")
        package.setAttribute('unique-identifier', "BookId")
        package.setAttribute('xmlns', "http://www.idpf.org/2007/opf")
        metadata = doc.createElement('metadata')
        metadata.setAttribute('xmlns:dc', "http://purl.org/dc/elements/1.1/")
        metadata.setAttribute('xmlns:opf', "http://www.idpf.org/2007/opf")
        unique = doc.createElement("dc:identifier")
        unique.setAttribute("id", "BookId")
        unique.setAttribute("opf:scheme", "UUID")
        unique.appendChild(doc.createTextNode(self.uid))
        metadata.appendChild(unique)
        manifest = doc.createElement('manifest')
        spine = doc.createElement('spine')
        spine.setAttribute("toc", "ncx")
        guide = doc.createElement('spine')
        package.appendChild(metadata)
        package.appendChild(manifest)
        package.appendChild(spine)
        package.appendChild(guide)
        doc.appendChild(package)
        self.writestr(self.opf_path, doc.toxml('UTF-8'))

    def _init_ncx(self):
        # TODO
        pass

    def _containerxml(self):
        template = """<?xml version="1.0" encoding="UTF-8"?>
    <container version="1.0"
               xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
        <rootfiles>
             <rootfile full-path="%s"
                       media-type="application/oebps-package+xml"/>
        </rootfiles>
    </container>"""
        return template % self.opf_path

    def addItem(self):
        """
        Add a file to manifest only
        """
        # TODO
        pass

    def addPart(self):
        """
        Add a file to manifest, spine and toc
        """
        # TODO
        pass
