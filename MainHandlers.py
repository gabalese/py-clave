import tornado.web
from utils import EPUB
from utils import listEpubFiles
import json


class ErrorHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, status_code):
        tornado.web.RequestHandler.__init__(self, application, request)
        self.set_status(status_code)

    def write_error(self, status, **kwargs):
        self.write("Nope.")

    def prepare(self):
        raise tornado.web.HTTPError(self._status_code)


class GetInfo(tornado.web.RequestHandler):
    def get(self, filename):
        if filename:
            try:
                m = EPUB(filename)
            except IOError:
                raise tornado.web.HTTPError(404)
            self.write(m.__dict__)
        else:
            raise tornado.web.HTTPError(400)


class ListFiles(tornado.web.RequestHandler):
    def get(self):
        response = listEpubFiles("epub")
        dump = json.JSONEncoder().encode(response)
        self.set_header("Content-Type", "application/json")
        self.write(dump)


class ShowFileToc(tornado.web.RequestHandler):
    def get(self, filename):
        try:
            toc = EPUB(filename).showToc()
            self.set_header("Content-Type","application/json")
            self.write(json.JSONEncoder().encode(toc))
        except IOError:
            raise tornado.web.HTTPError(404)


