import json
import os
import re

from threading import Thread
import tornado.web
import tornado.ioloop as IOLoop

from epub.utils import EPUB
from epub.utils import listFiles

from data.utils import opendb, DBNAME, EPUB_FILES_PATH


class GeneralErrorHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, status_code):
        tornado.web.RequestHandler.__init__(self, application, request)
        self.set_status(status_code)

    def write_error(self, status, **kwargs):
        self.write("Nope.")

    def prepare(self):
        raise tornado.web.HTTPError(400)


class GetInfo(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    def get(self, filename):
        if filename:

            try:
                self.thread = Thread(target=self.querydb, args=(self.on_callback, filename,))
                self.thread.start()
            except IOError:
                raise tornado.web.HTTPError(404)
        else:
            raise tornado.web.HTTPError(400)

    def querydb(self, callback, isbn):
        database, conn = opendb(DBNAME)

        try:
            path = database.execute("SELECT path FROM books WHERE isbn = '{0}' ".format(isbn)).fetchone()["path"]
        except TypeError:
            tornado.ioloop.IOLoop.instance().add_callback(lambda: callback("Nope."))
            raise tornado.web.HTTPError(404)
        finally:
            conn.close()

        output = EPUB(os.path.join(EPUB_FILES_PATH, path)).meta
        tornado.ioloop.IOLoop.instance().add_callback(lambda: callback(output))

    def on_callback(self, output):
        self.write(output)
        self.flush()
        self.finish()


class ListFiles(tornado.web.RequestHandler):

    def get(self):
        response = listFiles()
        dump = json.JSONEncoder().encode(response)
        self.set_header("Content-Type", "application/json")
        self.write(dump)


class ShowFileToc(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    def get(self, identifier):
        if identifier:
            try:
                self.thread = Thread(target=self.perform, args=(self.on_callback, identifier,))
                self.thread.start()
            except IOError:
                raise tornado.web.HTTPError(404)
        else:
            raise tornado.web.HTTPError(400)

    def perform(self, callback, identifier):
        database, conn = opendb(DBNAME)
        try:
            path = database.execute("SELECT path FROM books WHERE isbn = '{0}'".format(identifier)).fetchone()["path"]
        except TypeError:
            output = ""
            tornado.ioloop.IOLoop.instance().add_callback(lambda: callback("Nope."))
            raise tornado.web.HTTPError(404)
        finally:
            conn.close()

        output = EPUB(os.path.join(EPUB_FILES_PATH, path)).contents
        tornado.ioloop.IOLoop.instance().add_callback(lambda: callback(output))

    def on_callback(self, output):
        self.set_header("Content-Type", "application/json")
        self.write(json.JSONEncoder().encode(output))
        self.flush()
        self.finish()


class GetFilePart(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    def get(self, identifier, part):
        if identifier and part:
            try:
                self.thread = Thread(target=self.perform, args=(self.on_callback, identifier, part,))
                self.thread.start()
            except IOError:
                raise tornado.web.HTTPError(404)
        else:
            raise tornado.web.HTTPError(400)

    def perform(self, callback, identifier, part):
        database, conn = opendb(DBNAME)
        try:
            path = database.execute("SELECT path FROM books WHERE isbn = '{0}'".format(identifier)).fetchone()["path"]
        except TypeError:
            output = ""
            tornado.ioloop.IOLoop.instance().add_callback(lambda: callback("Nope."))
            raise tornado.web.HTTPError(404)
        finally:
            conn.close()
        try:
            epub = EPUB(os.path.join(EPUB_FILES_PATH, path))
            part_path = ""
            for i in epub.contents:
                if part in i.keys():
                    part_path = i[part]
            output = epub.read(part_path)

            output = re.sub(r'href="(.*?)"', 'href="/getpath/{0}/\g<1>"'.format(identifier), output)
            output = re.sub(r"href='(.*?)'", 'href="/getpath/{0}/\g<1>"'.format(identifier), output)
            # When a browser GETs a HTML, it also call every external resource declared in href=""s
            # When a relative path gets called, the browser appends the path to the getpart/xxx and raises a 404
            # I'll figure it out, eventually.

        except KeyError:
            output = "Nope."
            raise tornado.web.HTTPError(404)

        tornado.ioloop.IOLoop.instance().add_callback(lambda: callback(output))

    def on_callback(self, output):
        self.set_header("Content-Type", "text/html")
        self.write(output)
        self.flush()
        self.finish()


class GetFilePath(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    def get(self, identifier, part):
        if identifier and part:
            try:
                self.thread = Thread(target=self.perform, args=(self.on_callback, identifier, part,))
                self.thread.start()
            except IOError:
                raise tornado.web.HTTPError(404)
        else:
            raise tornado.web.HTTPError(400)

    def perform(self, callback, identifier, part):
        database, conn = opendb(DBNAME)
        try:
            path = database.execute("SELECT path FROM books WHERE isbn = '{0}'".format(identifier)).fetchone()["path"]
        except TypeError:
            output = ""
            tornado.ioloop.IOLoop.instance().add_callback(lambda: callback("Nope."))
            raise tornado.web.HTTPError(404)
        finally:
            conn.close()
        filepath = ""
        try:
            epub = EPUB(os.path.join(EPUB_FILES_PATH, path))
            for i in epub.namelist():
                if i.endswith(part):
                    filepath = i
            output = epub.read(filepath)

        except KeyError:
            print filepath
            pass

        finally:
            tornado.ioloop.IOLoop.instance().add_callback(lambda: callback(output))

    def on_callback(self, output):
        self.set_header("Content-Type", "text/html")
        self.write(output)
        self.flush()
        self.finish()
