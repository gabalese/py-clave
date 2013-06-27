import tornado.ioloop
import sys
from TestHandlers import Echo, MainHandler, PingHandler
from MainHandlers import GetInfo, ErrorHandler

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/echo", Echo),
    (r"/ping",PingHandler),
    (r"/info/(.*)", GetInfo)
])

tornado.web.ErrorHandler = ErrorHandler

if __name__ == "__main__":
    try:
        port = sys.argv[1]
    except:
        port = 8080
    application.listen(port)
    tornado.ioloop.IOLoop.instance().start()