import sys
import os
from threading import Thread

import tornado.web
import tornado.ioloop

from controllers.TestHandlers import PingHandler, CheckDB
from controllers.MainHandlers import GetInfo, GeneralErrorHandler, ListFiles, \
    ShowFileToc, GetFilePart, GetFilePath, DownloadPublication, OPDSCatalogue, ShowManifest, GetResource, MainQuery, \
    MainHandler, DownloadWithExLibris

import template.module.ui as UI

from data.opds import updateCatalog
from data.utils import updateDB
from data.data import PORT, DB_UPDATE_TIMEOUT, FEED_UPDATE_TIMEOUT


application = tornado.web.Application([
    (r"/", MainHandler),
    #  Test
    (r"/ping", PingHandler),
    (r"/checkdb", CheckDB),
    #  OPDS Catalogue
    (r"/opds-catalog", OPDSCatalogue),
    (r"/catalogue/opds", OPDSCatalogue),
    #  Metadata
    (r"/catalogue", ListFiles),
    (r"/book/([^/]+$)", GetInfo),
    #  Get whole book
    (r"/book/([^/]+)/download", DownloadPublication),
    (r"/book/([^/]+)/download/exlibris", DownloadWithExLibris),
    #  Show toc
    (r"/book/([^/]+)/toc", ShowFileToc),
    #  Query titles
    (r"/catalogue/search", MainQuery),
    #  Show manifest
    (r"/book/([^/]+)/manifest", ShowManifest),
    (r"/book/([^/]+)/manifest/([^/]+)", GetResource),
    #  Parts
    (r"/book/([^/]+)/chapter/([^/]+)", GetFilePart),
    (r"/book/([^/]+)/chapter/([^/]+)/fragment/([^/]+)", GetFilePart),
    #  Resolution fallback
    (r"/getpath/([^/]+)/(.+)", GetFilePath)],
    debug=True,
    cookie_secret="ed54ef7408cd7eeeb5a819ddcc633550",  # TODO
    login_url="/login",  # TODO
    ui_modules={"Hello": UI.Hello},
    template_path=os.path.join(os.path.dirname(__file__), "template"),
    static_path=os.path.join(os.path.dirname(__file__), "static"))

tornado.web.ErrorHandler = GeneralErrorHandler

if __name__ == "__main__":

    application.listen(PORT)

    try:
        def new_thread_wrapper(func):
            x = Thread(target=func)
            x.start()

        def update_db_new_thread():
            x = Thread(target=updateDB)
            x.start()

        def update_xml_feed():
            x = Thread(target=updateCatalog)
            x.start()

        update_db_new_thread()

        periodic = tornado.ioloop.PeriodicCallback(update_db_new_thread, DB_UPDATE_TIMEOUT)
        periodic.start()

        update_xml = tornado.ioloop.PeriodicCallback(update_xml_feed, FEED_UPDATE_TIMEOUT)
        update_xml.start()

        tornado.ioloop.IOLoop.instance().start()

    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().close()

    except Exception as e:
        print "Uncaught exception"
        print e
        tornado.ioloop.IOLoop.instance().close()
