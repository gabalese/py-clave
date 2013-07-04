import json
from threading import Thread

import tornado.web
import tornado.ioloop as IOLoop

from epub.utils import EPUB
from epub.utils import listFiles

from data.utils import opendb, DBNAME


class ErrorHandler(tornado.web.RequestHandler):
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
                #self.flush()
            except IOError:
                raise tornado.web.HTTPError(404)
        else:
            raise tornado.web.HTTPError(400)

    def querydb(self, callback, isbn):
        database, conn = opendb(DBNAME)
        path = database.execute("SELECT path FROM books WHERE isbn = '{0}' ".format(isbn)).fetchone()["path"]
        output = EPUB(path).meta
        tornado.ioloop.IOLoop.instance().add_callback(lambda: callback(output))

    def on_callback(self, output):
        self.set_header("Content-Type", "application/json")  # when async, no auto json if dict
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
    def get(self, filename):
        try:
            toc = EPUB(filename).contents
            response = json.JSONEncoder().encode(toc)
            self.write(response)
        except IOError:
            raise tornado.web.HTTPError(404)
