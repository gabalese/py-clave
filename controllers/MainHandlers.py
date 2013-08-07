import json
import xml.etree.ElementTree as ET
import re
import os
from cStringIO import StringIO
import time

import tornado.web
from tornado import gen

from epub import EPUB
from epub.utils import listFiles

from data.utils import opendb
from data.data import DatabaseConnection
from data import opds

from urlparse import parse_qs as parse_querystring


def accepted_formats(header):
    header_list = header.split(",")
    for i, v in enumerate(header_list):
        header_list[i] = v.split(";")[0].strip()
    return header_list


class GeneralErrorHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, status_code):
        tornado.web.RequestHandler.__init__(self, application, request)
        self.set_status(status_code)

    def write_error(self, status, **kwargs):
        self.write("Bad request")

    def prepare(self):
        raise tornado.web.HTTPError(400)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("hello.html", title="Welcome!", user=self.request.remote_ip)


class GetInfo(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self, filename):
        if filename:
            response = yield gen.Task(self.querydb, filename)
            if "text/html" in accepted_formats(self.request.headers.get("accept")):
                self.render("info.html",
                            title=response["metadata"]["title"],
                            id=response["id"],
                            meta=response["metadata"],
                            contents=response["toc"],
                            manifest=response["manifest"],
                            cover=response["cover"]
                            )
            else:
                output = response
                output["cover"] = "/book/{0}/manifest/{1}".format(response["id"], response["cover"])
                self.write(json.dumps(output))
                self.finish()
        else:
            raise tornado.web.HTTPError(400)

    def querydb(self, isbn, callback):
        database, conn = opendb()
        try:
            path = database.execute("SELECT path FROM books WHERE isbn = ? ", (isbn,)).fetchone()["path"]
        except TypeError:
            raise tornado.web.HTTPError(404)
        finally:
            conn.close()
        epubfile = EPUB(path)
        output = epubfile.info
        output["cover"] = epubfile.cover
        output["id"] = epubfile.id
        output["toc"] = epubfile.contents
        return callback(output)


class ShowManifest(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self, filename):
        if filename:
            response = yield gen.Task(self.querydb, filename)
            self.set_header("Content-Type", "application/json")
            self.set_header("Charset", "UTF-8")
            self.write(json.dumps(response))
            self.finish()
        else:
            raise tornado.web.HTTPError(400)

    def querydb(self, isbn, callback):
        database, conn = opendb()
        try:
            path = database.execute("SELECT path FROM books WHERE isbn = ? ", (isbn,)).fetchone()["path"]
        except TypeError:
            raise tornado.web.HTTPError(404)
        finally:
            conn.close()
        epubfile = EPUB(path)
        output = epubfile.info["manifest"]
        return callback(output)


class ListFiles(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        response = yield gen.Task(self.cataloguedump)
        if "text/html" in accepted_formats(self.request.headers.get("accept")):
            self.render("catalogue.html",
                        output=response, search=False)
        else:
            dump = json.JSONEncoder().encode(response)
            self.set_header("Content-Type", "application/json")
            self.set_header("Charset", "UTF-8")
            self.write(dump)
            self.finish()

    def cataloguedump(self, callback):
        response = listFiles()
        return callback(response)


class ShowFileToc(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self, identifier):
        if identifier:
            try:
                output = yield gen.Task(self.queryToc, identifier)
                self.set_header("Content-Type", "application/json")
                self.write(json.JSONEncoder().encode(output))
                self.finish()
            except IOError:
                raise tornado.web.HTTPError(404)
        else:
            raise tornado.web.HTTPError(400)

    def queryToc(self, identifier, callback):
        database, conn = opendb()
        try:
            path = database.execute("SELECT path FROM books WHERE isbn = ?", (identifier, )).fetchone()["path"]
        except TypeError:
            raise tornado.web.HTTPError(404)
        finally:
            conn.close()
        output = EPUB(path).contents
        return callback(output)


class GetFilePart(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self, identifier, part, section=False):
        if identifier and part and not section:
            try:
                output = yield gen.Task(self.perform, identifier, part, section=False)
            except IOError:
                raise tornado.web.HTTPError(404)
        elif identifier and part and section:
            try:
                output = yield gen.Task(self.perform, identifier, part, section)
            except IOError:
                raise tornado.web.HTTPError(404)
        else:
            raise tornado.web.HTTPError(405)

        self.set_header("Content-Type", "text/html")
        self.set_header("Charset", "UTF-8")
        self.write(output)
        self.finish()

    def perform(self, identifier, part, section, callback):
        database, conn = opendb()
        try:
            path = database.execute("SELECT path FROM books WHERE isbn = ?", (identifier, )).fetchone()["path"]
        except TypeError:
            raise tornado.web.HTTPError(404)
        finally:
            conn.close()
        try:
            epub = EPUB(path)
            part_path = ""
            for i in epub.contents:
                if part == i.get("id"):
                    part_path = i.get("src")
            output = epub.read(re.sub(r"#(.*)", "", part_path))  # strip fragment id.

            output = re.sub(r'(href|src)="(\.\./)?(.*?)"', '\g<1>="/getpath/{0}/\g<3>"'.format(identifier), output)
            output = re.sub(r"(href|src)='(\.\./)?(.*?)'", '\g<1>="/getpath/{0}/\g<3>"'.format(identifier), output)

            if section:
                try:
                    from htmlentitydefs import entitydefs
                    parser = ET.XMLParser()
                    parser.parser.UseForeignDTD(True)
                    parser.entity.update(entitydefs)
                    source = StringIO(output)
                    root = ET.parse(source, parser)
                    section = int(section) - 1
                    name = root.find(".//{http://www.w3.org/1999/xhtml}body")[section]
                    output = " ".join([t for t in list(name.itertext())])
                except Exception, e:
                    print e
                    raise tornado.web.HTTPError(404)

        except KeyError:
            raise tornado.web.HTTPError(404)

        return callback(output)


class GetFilePath(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self, identifier, part):
        if identifier and part:
            try:
                output = yield gen.Task(self.perform, identifier, part)
                self.set_header("Content-Type", "text/html")
                self.write(output)
                self.finish()
            except IOError:
                raise tornado.web.HTTPError(404)
        else:
            raise tornado.web.HTTPError(400)

    def perform(self, identifier, part, callback):
        database, conn = opendb()
        try:
            path = database.execute("SELECT path FROM books WHERE isbn = '{0}'".format(identifier)).fetchone()["path"]
        except TypeError:
            raise tornado.web.HTTPError(404)
        finally:
            conn.close()
        filepath = ""
        try:
            epub = EPUB(path)
            for i in epub.namelist():
                if i.endswith(part):
                    filepath = i
            output = epub.read(filepath)

        except KeyError:
            output = "Nope."
            pass
        return callback(output)


class GetResource(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self, identifier, manifest_id):
        if identifier and manifest_id:
            try:
                output, mimetype = yield gen.Task(self.perform, identifier, manifest_id)
                self.set_header("Content-Type", mimetype)
                self.write(output)
                self.finish()
            except IOError:
                raise tornado.web.HTTPError(404)
        else:
            raise tornado.web.HTTPError(400)

    def perform(self, identifier, toc_id, callback):
        database, conn = opendb()
        try:
            path = database.execute("SELECT path FROM books WHERE isbn = '{0}'".format(identifier)).fetchone()["path"]
        except TypeError:
            raise tornado.web.HTTPError(404)
        finally:
            conn.close()
        filepath = ""
        mimetype = ""
        try:
            epub = EPUB(path)
            for i in epub.info["manifest"]:
                if i["id"] == toc_id:
                    filepath = i["href"]
                    mimetype = i["mimetype"]
            if not mimetype:
                mimetype = "text/html"
            output = epub.read(os.path.join(epub.root_folder, filepath)), mimetype

        except KeyError:
            output = "KEY ERROR"
            pass
        return callback(output)


class DownloadPublication(tornado.web.RequestHandler):

    def get(self, filename):
        if filename:
            database, conn = opendb()
            try:
                path = database.execute("SELECT path FROM books WHERE isbn = '{0}' ".format(filename)).fetchone()["path"]
            except TypeError:
                raise tornado.web.HTTPError(404)
            finally:
                conn.close()
            output = open(path, "r")
            self.set_header('Content-Type', 'application/zip')
            self.set_header('Content-Disposition', 'attachment; filename='+os.path.basename(path)+'')
            self.write(output.read())
        else:
            raise tornado.web.HTTPError(404)


class OPDSCatalogue(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        if os.path.exists("feed.xml") and (time.time() - os.path.getmtime("feed.xml")) < 200:
            self.set_header("Content-Type", "application/atom+xml")
            with open("feed.xml", "r") as f:
                self.write(f.read())
                self.finish()
        else:
            catalogue = yield gen.Task(self.perform, )
            self.set_header("Content-Type", "application/atom+xml")
            self.write(catalogue)
            self.finish()

    def perform(self, callback):
        catalogue = opds.generateCatalogRoot()
        #  Raw cache. TODO: better cache handling
        with open("feed.xml", "w") as f:
            f.write(catalogue)
        return callback(catalogue)


class MainQuery(tornado.web.RequestHandler):

    def get(self):
        query = parse_querystring(self.request.query)
        if not query:
            self.redirect("/catalogue")
        connessione = DatabaseConnection()
        result = connessione.query(query.keys()[0], query.values()[0][0])
        meta = {}
        for entry in result:
            meta[entry["isbn"]] = [entry["title"], os.path.basename(entry["path"]), entry["author"]]
        connessione.exit()
        if "text/html" in accepted_formats(self.request.headers.get("accept")):
            self.render("catalogue.html", output=meta, search=query.values()[0][0])
        else:
            self.write(meta)
