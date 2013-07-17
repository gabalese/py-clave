import json
import xml.etree.ElementTree as ET
import re
import os

import tornado.web
from tornado import gen

from epub.utils import EPUB
from epub.utils import listFiles

from data.utils import opendb
from data import opds


class GeneralErrorHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, status_code):
        tornado.web.RequestHandler.__init__(self, application, request)
        self.set_status(status_code)

    def write_error(self, status, **kwargs):
        self.write("Bad request")

    def prepare(self):
        raise tornado.web.HTTPError(400)


class GetInfo(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self, filename):
        if filename:
            response = yield gen.Task(self.querydb, filename)
            self.write(response)
            self.finish()
        else:
            raise tornado.web.HTTPError(400)

    def querydb(self, isbn, callback):
        database, conn = opendb()
        try:
            path = database.execute("SELECT path FROM books WHERE isbn = '{0}' ".format(isbn)).fetchone()["path"]
        except TypeError:
            raise tornado.web.HTTPError(404)
        finally:
            conn.close()
        output = EPUB(path).meta
        return callback(output)


class ListFiles(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        response = yield gen.Task(self.cataloguedump)
        dump = json.JSONEncoder().encode(response)
        self.set_header("Content-Type", "application/json")
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
            path = database.execute("SELECT path FROM books WHERE isbn = '{0}'".format(identifier)).fetchone()["path"]
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
        self.set_header("Charset","UTF-8")
        self.write(output)
        self.finish()

    def perform(self, identifier, part, section, callback):
        database, conn = opendb()
        try:
            path = database.execute("SELECT path FROM books WHERE isbn = '{0}'".format(identifier)).fetchone()["path"]
        except TypeError:
            raise tornado.web.HTTPError(404)
        finally:
            conn.close()
        try:
            epub = EPUB(path)
            part_path = ""
            for i in epub.contents:
                if part in i.keys():
                    part_path = i[part]
            output = epub.read(re.sub(r"#(.*)", "", part_path))  # strip fragment id.

            output = re.sub(r'(href|src)="(.*?)"', '\g<1>="/getpath/{0}/\g<2>"'.format(identifier), output)
            output = re.sub(r"(href|src)='(.*?)'", '\g<1>="/getpath/{0}/\g<2>"'.format(identifier), output)

            if section:
                try:
                    root = ET.fromstring(output)
                    section = int(section) - 1
                    name = root.find(".//{http://www.w3.org/1999/xhtml}body")[section]
                    output = " ".join([t for t in list(name.itertext())])
                except:
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
                self.flush()
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
        catalogue = yield gen.Task(self.perform, )
        self.set_header("Content-Type", "application/atom+xml")
        self.write(catalogue)
        self.finish()

    def perform(self, callback):
        catalogue = opds.generateCatalogRoot()
        return callback(catalogue)
