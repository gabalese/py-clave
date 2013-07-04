import json
from threading import Thread
import tornado.web
import tornado.ioloop as IOLoop

from epub.utils import EPUB
from epub.utils import listFiles

from data.utils import opendb, DBNAME


class GeneralErrorHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, status_code):
        tornado.web.RequestHandler.__init__(self, application, request)
        self.set_status(status_code)

    def write_error(self, status, **kwargs):
        self.write("Nope.")

    def prepare(self):
        raise tornado.web.HTTPError(self._status_code)


class GetInfo(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    def get(self, filename):
        if filename:

            try:
                self.thread = Thread(target=self.querydb, args=(self.on_callback,filename,))
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

        output = EPUB(path).meta
        tornado.ioloop.IOLoop.instance().add_callback(lambda: callback(output))

    def on_callback(self, output):
        self.write(output)
        self.flush()
        self.finish()


class ListFiles(tornado.web.RequestHandler):

    def get(self):
        response = listFiles("epub")
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
            path = database.execute("SELECT path FROM books WHERE isbn = {0}".format(identifier)).fetchone()["path"]
        except TypeError:
            output = ""
            tornado.ioloop.IOLoop.instance().add_callback(lambda: callback("Nope."))
            raise tornado.web.HTTPError(404)
        finally:
            conn.close()

        output = EPUB(path).contents
        tornado.ioloop.IOLoop.instance().add_callback(lambda: callback(output))

    def on_callback(self, output):
        self.set_header("Content-Type","application/json")
        self.write(json.JSONEncoder().encode(output))
        self.flush()
        self.finish()
