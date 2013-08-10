import zipfile as ZIP
import os
import re
import uuid
from StringIO import StringIO
import datetime

from xml.dom import minidom
import xml.etree.ElementTree as ET

TMP = {"opf": None, "ncx": None}
FLO = None

NAMESPACE = {
    "dc": "{http://purl.org/dc/elements/1.1/}",
    "opf": "{http://www.idpf.org/2007/opf}",
    "ncx": "{http://www.daisy.org/z3986/2005/ncx/}"
}


class InvalidEpub(Exception):
    pass


class EPUB(ZIP.ZipFile):
    """
    EPUB file representation class.

    """
    def __init__(self, filename, mode="r"):
        """
        Global Init Switch

        :type filename: str or StringIO
        :param filename: File to be processed
        :type mode: str
        :param mode: "w" or "r", mode to init the zipfile
        """
        if mode == "w":
            assert not os.path.exists(filename), "Can't overwrite existing file: %s" % filename
            self.filename = filename
            ZIP.ZipFile.__init__(self, self.filename, mode="w")
            self.__init__write()
        if mode == "a":
            ZIP.ZipFile.__init__(self, filename, mode="a")
            self.__init__read(filename)
        else:  # retrocompatibility?
            ZIP.ZipFile.__init__(self, filename, mode="r")
            self.__init__read(filename)

    def __init__read(self, filename):
        """
        Constructor to initialize the zipfile in read-only mode

        :type filename: str or StringIO
        :param filename: File to be processed
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
            self.opf_path = ET.fromstring(f)[0][0].get("full-path")
        except IndexError:
            #  ...else the file is invalid.
            print "The %s file is not a valid OCF." % str(filename)
            raise InvalidEpub

        # NEW: json-able info tree
        self.info = {"metadata": {},
                     "manifest": [],
                     "spine": [],
                     "guide": []}

        self.root_folder = os.path.dirname(self.opf_path)   # Used to compose absolute paths for reading in zip archive
        self.opf = ET.fromstring(self.read(self.opf_path))  # OPF tree

        ns = re.compile(r'\{.*?\}')  # RE to strip {namespace} mess

        # Iterate over <metadata> section, fill EPUB.info["metadata"] dictionary
        for i in self.opf.find("{0}metadata".format(NAMESPACE["opf"])):
            tag = ns.sub('', i.tag)
            if tag not in self.info["metadata"]:
                self.info["metadata"][tag] = i.text or i.attrib
            else:
                self.info["metadata"][tag] = [self.info["metadata"][tag], i.text or i.attrib]

        # Get id of the cover in <meta name="cover" />
        try:
            coverid = self.opf.find('.//*[@name="cover"]').get("content")
        except AttributeError:
            # It's a facultative field, after all
            coverid = None
        self.cover = coverid  # This is the manifest ID of the cover

        self.info["manifest"] = [{"id": x.get("id"),                # Build a list of manifest items
                                  "href": x.get("href"),
                                  "mimetype": x.get("media-type")}
                                 for x in self.opf.find("{0}manifest".format(NAMESPACE["opf"]))]

        self.info["spine"] = [{"idref": x.get("idref")}             # Build a list of spine items
                              for x in self.opf.find("{0}spine".format(NAMESPACE["opf"]))]
        try:
            self.info["guide"] = [{"href": x.get("href"),           # Build a list of guide items
                                   "type": x.get("type"),
                                   "title": x.get("title")}
                                  for x in self.opf.find("{0}guide".format(NAMESPACE["opf"]))]
        except TypeError:                                           # The guide element is optional
            self.info["guide"] = None

        # Document identifier
        try:
            self.id = self.opf.find('.//*[@id="{0}"]'.format(self.opf.get("unique-identifier"))).text
        except AttributeError:
            raise InvalidEpub                                       # Cannot process an EPUB without unique-identifier
                                                                    # attribute of the package element
        # Get and parse the TOC
        toc_id = self.opf[2].get("toc")
        expr = ".//*[@id='{0:s}']".format(toc_id)
        toc_name = self.opf.find(expr).get("href")
        self.ncx_path = self.root_folder + "/" + toc_name
        self.ncx = ET.fromstring(self.read(self.ncx_path))
        self.contents = [{"name": i[0][0].text or "None",           # Build a list of toc elements
                          "src": self.root_folder + "/" + i[1].get("src"),
                          "id":i.get("id")}
                         for i in self.ncx.iter("{0}navPoint".format(NAMESPACE["ncx"]))]    # The iter method
                                                                                            # loops over nested
                                                                                            # navPoints

    def __init__write(self):
        """
        Init an empty EPUB

        """
        self.opf_path = "OEBPS/content.opf"  # Define a default folder for contents
        self.ncx_path = "OEBPS/toc.ncx"
        self.root_folder = "OEBPS"
        self.uid = '%s' % uuid.uuid4()

        self.info = {"metadata": {},
                     "manifest": [],
                     "spine": [],
                     "guide": []}

        self.writestr('mimetype', "application/epub+zip")
        self.writestr('META-INF/container.xml', self._containerxml())
        self.info["metadata"]["creator"] = "py-clave server"
        self.info["metadata"]["title"] = ""
        self.info["metadata"]["language"] = ""

        # Problem is: you can't overwrite file contents with python ZipFile
        # so you must add contents BEFORE finalizing the file
        # calling close() method.

        self.opf = ET.fromstring(self._init_opf())  # opf property is always a ElementTree
        self.ncx = ET.fromstring(self._init_ncx())  # so is ncx. Consistent with self.(opf|ncx) built by __init_read()

    def close(self):
        if self.fp is None:     # Check file status
            return
        if self.mode == "r":    # check file mode
            ZIP.ZipFile.close(self)
            return
        else:
            try:
                global TMP                  # in-memory copy of existing opf-ncx. When the epub gets re-init,
                                            # it loses track of modifications
                TMP["opf"] = self.opf
                TMP["ncx"] = self.ncx
                self._safeclose()
                ZIP.ZipFile.close(self)     # give back control to superclass close method
            except RuntimeError:            # zipfile.__del__ destructor calls close(), ignore
                return

    def _safeclose(self):
        """
        Preliminary operations before closing an EPUB
        Writes the empty or modified opf-ncx files before closing the zipfile
        """
        if self.mode == "a":  # no need to do that if dealing with mode=w files
            self._delete(self.opf_path, self.ncx_path)  # see following horrible hack:
                                                        # zipfile cannot manage overwriting on the archive
                                                        # this basically RECREATES the epub from scratch
                                                        # and is sure slow as hell
                                                        # ... and a recipe for disaster.
            self.opf = TMP["opf"]
            self.ncx = TMP["ncx"]  # get back the temporary copies

        self.writestr(self.opf_path, ET.tostring(self.opf, encoding="UTF-8"))
        self.writestr(self.ncx_path, ET.tostring(self.ncx, encoding="UTF-8"))
        self.__init__read(FLO)  # We may still need info dict of a closed EPUB

    def _init_opf(self):
        """
        Constructor for empty OPF
        :type return: xml.minidom.Document
        :return: xml.minidom.Document
        """
        today = datetime.date.today()
        opf_tmpl = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
                        <package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="2.0">
                        <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
                            <dc:identifier id="BookId" opf:scheme="UUID">{uid}</dc:identifier>
                            <dc:title>{title}</dc:title>
                            <dc:language>{lang}</dc:language>
                            <dc:date opf:event="modification">{date}</dc:date>
                        </metadata>
                        <manifest>
                            <item href="toc.ncx" id="ncx" media-type="application/x-dtbncx+xml" />
                        </manifest>
                        <spine toc="ncx">
                        </spine>
                        <guide>
                        </guide>
                        </package>"""
        doc = minidom.parseString(opf_tmpl.format(uid=self.uid,
                                                  date=today,
                                                  title=self.info["metadata"]["title"],
                                                  lang=self.info["metadata"]["language"]
                                                  ))
        return doc.toxml('UTF-8')

    def _init_ncx(self):
        """
        Constructor for empty OPF
        :type return: xml.minidom.Document
        :return: xml.minidom.Document
        """
        ncx_tmpl = """<?xml version="1.0" encoding="utf-8"?>
                        <!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
                           "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
                        <ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
                        <head>
                           <meta name="dtb:uid" content="{uid}" />
                           <meta name="dtb:depth" content="0" />
                           <meta name="dtb:totalPageCount" content="0" />
                           <meta name="dtb:maxPageNumber" content="0" />
                        </head>
                        <docTitle>
                           <text>{title}</text>
                        </docTitle>
                        <navMap>
                        </navMap>
                        </ncx>"""
        ncx = minidom.parseString(ncx_tmpl.format(uid=self.uid, title="Default"))
        return ncx.toxml('UTF-8')

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

    def _delete(self, *paths):
        """
        Delete archive member
        Basically a hack: zince zipfile can't natively overwrite or delete resources,
        a new archive is created from scratch to a StringIO file object.
        The starting file is *never* overwritten.
        To write the new file to disk, use the writefiletodisk() instance method.

        :type paths: str
        :param paths: files to be deleted inside EPUB file
        """
        global FLO  # File-Like-Object: this is obviously wrong: any better idea?
                    # Also, the variable name is questionable
        FLO = StringIO()
        new_zip = ZIP.ZipFile(FLO, 'w')
        for item in self.infolist():
            if item.filename not in paths:
                new_zip.writestr(item.filename, self.read(item.filename))
        ZIP.ZipFile.close(self)     # Don't know why
        new_zip.close()             # but it works, don't ever touch
        ZIP.ZipFile.__init__(self, FLO, mode="a")

    def additem(self, fileObject, href, mediatype):
        """
        Add a file to manifest only

        :type fileObject: StringIO
        :param fileObject:
        :type href: str
        :param href:
        :type mediatype: str
        :param mediatype:
        """
        assert self.mode != "r", "%s is not writable" % self
        element = ET.Element("item", attrib={"id": str(uuid.uuid4())[:5], "href": href, "media-type": mediatype})
        self.writestr(os.path.join(self.root_folder, element.attrib["href"]), fileObject.getvalue())
        self.opf[1].append(element)

    def addpart(self, fileObject, href, mediatype, position=None, type="text"):
        assert self.mode == "w", "%s is not writable" % self
        # TODO

    def writetodisk(self, filename):
        f = open(filename, "w")
        self.filename.seek(0)
        f.write(self.filename.read())
        f.close()
