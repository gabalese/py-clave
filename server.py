import sys

import tornado.web
import tornado.ioloop
from threading import Thread

from controllers.TestHandlers import MainHandler, PingHandler, CheckDB
from controllers.MainHandlers import GetInfo, GeneralErrorHandler, ListFiles, ShowFileToc

from data.utils import updateDB, DBNAME


application = tornado.web.Application([
    (r"/", MainHandler),
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
        def update_db_new_thread():
            x = Thread(target=updateDB(DBNAME))
            x.start()
        update_db_new_thread()

        periodic = tornado.ioloop.PeriodicCallback(update_db_new_thread, 2000)  # sub-optimal
        periodic.start()

        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().close()
