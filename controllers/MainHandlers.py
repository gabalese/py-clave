import json
from threading import Thread

import tornado.web
import tornado.ioloop as IOLoop

from epub.utils import EPUB
from epub.utils import listEpubFiles


# class DelegationHandler(tornado.web.RequestHandler):
#     def perform(self, callback):
#         #do something
#         # ... then return to main IOLoop instance
#         tornado.ioloop.IOLoop.instance().add_callback(lambda: callback(output))
#
#     @tornado.web.asynchronous
#     def get(self):
#         self.thread = Thread(target=self.perform, args=(self.on_callback,))
#         self.thread.start()
#         self.flush()  # required when async
#
#     def on_callback(self, output):
#         self.write(output)
#         self.finish()  # needed, when async is involved


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
            self.write(m.meta)
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
            toc = EPUB(filename).contents
            response = json.JSONEncoder().encode(toc)
            self.write(response)
        except IOError:
            raise tornado.web.HTTPError(404)
