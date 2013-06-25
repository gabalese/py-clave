import tornado.ioloop
import tornado.web
import sys

from utils import Metadata

class ErrorHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, status_code):
        tornado.web.RequestHandler.__init__(self, application, request)
        self.set_status(status_code)
    
    def write_error(self, status, **kwargs):
       self.write("Nope.")
    
    def prepare(self):
        raise tornado.web.HTTPError(self._status_code)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")
    
class Insulta(tornado.web.RequestHandler):
    def get(self):
        self.write(self.request.remote_ip+", LMMT")
        
class Echo(tornado.web.RequestHandler):
    def get(self):
        self.write("I hear you, ",self.request.remote_ip)
        
class GetInfo(tornado.web.RequestHandler):
    def get(self, filename):
        if filename:
            try:
                m = Metadata(filename)
            except IOError:
                raise tornado.web.HTTPError(404)
            response = m.author
            response += ", "+m.title
            self.write(response)
        else:
            self.write("Nothing to do")
    

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/echo", Echo),
    (r"/info/(.*)", GetInfo)
])

#tornado.web.ErrorHandler = ErrorHandler

if __name__ == "__main__":
    application.listen(8080)
    tornado.ioloop.IOLoop.instance().start()