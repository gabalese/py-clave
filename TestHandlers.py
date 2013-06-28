import tornado.web
import time


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("./public/index.html")


class Echo(tornado.web.RequestHandler):
    def get(self):
        self.write("I hear you, " + self.request.remote_ip)


class PingHandler(tornado.web.RequestHandler):
    def get(self):
        response = {"status": "200OK", "timestamp": time.time()}
        self.write(response)
