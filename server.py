import os
from multiprocessing import Process
import logging
import signal

import tornado.web
import tornado.ioloop

from controllers.TestHandlers import PingHandler, CheckDB
from controllers.MainHandlers import GetInfo, GeneralErrorHandler, ListFiles, \
    ShowFileToc, GetFilePart, GetFilePath, DownloadPublication, OPDSCatalogue, ShowManifest, GetResource, MainQuery, \
    MainHandler, DownloadWithExLibris, GetCover

import template.module.ui as UI

from data.utils import updateDB
from data.data import PORT, DB_UPDATE_TIMEOUT


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
    (r"/book/([^/]+)/cover", GetCover),
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


def worker_update_db():
    """Multiprocess'd database update"""
    x = Process(target=updateDB)
    x.start()


def stop_handler(sig, frame):
    """To stop the server on received SIGINT"""
    logging.warning('Caught signal: %s (%s), stopping server', sig, frame.f_lasti)
    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.add_callback(lambda x: x.stop(), ioloop)


def update_handler(sig, frame):
    """Update the server on USR1 signal"""
    logging.warning('Update signal received! %s (%s)', sig, frame.f_lasti)
    worker_update_db()

if __name__ == "__main__":

    application.listen(PORT)

    signal.signal(signal.SIGINT, stop_handler)      # kill -s INT
    signal.signal(signal.SIGTERM, stop_handler)     # kill -s TERM
    signal.signal(signal.SIGUSR1, update_handler)   # kill -s USR1

    try:
        worker_update_db()
        periodic = tornado.ioloop.PeriodicCallback(worker_update_db, DB_UPDATE_TIMEOUT)
        periodic.start()
        tornado.ioloop.IOLoop.instance().start()

    except Exception as e:
        print "Uncaught exception"
        logging.warning(e)
        tornado.ioloop.IOLoop.instance().close()
