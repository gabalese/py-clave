import tornado.web
import json
import time


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


class Echo(tornado.web.RequestHandler):
    def get(self):
        self.write("I hear you, " + self.request.remote_ip)


class PingHandler(tornado.web.RequestHandler):
    def get(self):
        response = {"status": "200OK", "timestamp": time.time()}
        self.write(json.JSONEncoder().encode(response))
