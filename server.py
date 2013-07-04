import sys

import tornado.web
import tornado.ioloop

from controllers.TestHandlers import Echo, MainHandler, PingHandler, CheckDB
from controllers.MainHandlers import GetInfo, GeneralErrorHandler, ListFiles, ShowFileToc

from data.utils import updateDB, DBNAME


application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/echo", Echo),
    (r"/ping", PingHandler),
    (r"/info/(.*)", GetInfo),
    (r"/list", ListFiles),
    (r"/toc/(.*)", ShowFileToc),
    (r"/checkdb", CheckDB),
    (r'/public/(.*)', tornado.web.StaticFileHandler, {'path': "./static"})
], debug=True)

tornado.web.ErrorHandler = GeneralErrorHandler

if __name__ == "__main__":
    try:
        port = sys.argv[1]
    except IndexError:
        port = 8080
    application.listen(port)
    try:
        updateDB(DBNAME, "epub")

        periodic = tornado.ioloop.PeriodicCallback(updateDB, 60000)
        periodic.start()

        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().close()
