import sys

import tornado.web
import tornado.ioloop
from threading import Thread

from controllers.TestHandlers import MainHandler, PingHandler, CheckDB
from controllers.MainHandlers import GetInfo, GeneralErrorHandler, ListFiles, \
    ShowFileToc, GetFilePart, GetFilePath, DownloadPublication, OPDSCatalogue, ShowManifest, GetResource, MainQuery

from data.utils import updateDB


application = tornado.web.Application([
    (r"/", MainHandler),
    #  Test
    (r"/ping", PingHandler),
    (r"/checkdb", CheckDB),
    #  OPDS Catalogue
    (r"/opds-catalog", OPDSCatalogue),
    #  Metadata
    (r"/catalogue", ListFiles),
    (r"/book/([^/]+$)", GetInfo),
    #  Get whole book
    (r"/book/([^/]+)/download", DownloadPublication),
    #  Show toc
    (r"/book/([^/]+)/toc", ShowFileToc),
    #  Query titles
    (r"/catalogue/search", MainQuery),
    (r"/catalogue/opds", OPDSCatalogue),
    #  Show manifest
    (r"/book/([^/]+)/manifest", ShowManifest),
    (r"/book/([^/]+)/manifest/([^/]+)", GetResource),
    #  Parts
    (r"/book/([^/]+)/chapter/([^/]+)", GetFilePart),
    (r"/book/([^/]+)/chapter/([^/]+)/fragment/([^/]+)", GetFilePart),
    #  Resolution fallback
    (r"/getpath/([^/]+)/(.+)", GetFilePath),
    (r'/public/([^/]+)', tornado.web.StaticFileHandler, {'path': "./static"})],
    debug=True, cookie_secret="ed54ef7408cd7eeeb5a819ddcc633550", login_url="/login", template_path="./template")

tornado.web.ErrorHandler = GeneralErrorHandler

if __name__ == "__main__":
    try:
        port = sys.argv[1]
    except IndexError:
        port = 8080
    try:
        timeout = int(sys.argv[2])
    except IndexError:
        timeout = 1000000
    finally:
        application.listen(port)

    try:
        def update_db_new_thread():
            x = Thread(target=updateDB)
            x.start()

        update_db_new_thread()

        periodic = tornado.ioloop.PeriodicCallback(update_db_new_thread, timeout)
        periodic.start()

        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().close()

    except Exception as e:
        print "Uncaught exception"
        print e
        tornado.ioloop.IOLoop.instance().close()
