import tornado.web
import time
from data.data import database, conn


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("./static/index.html")


class Echo(tornado.web.RequestHandler):
    def get(self):
        self.write("I hear you, " + self.request.remote_ip)


class PingHandler(tornado.web.RequestHandler):
    def get(self):
        response = {"status": "200OK", "timestamp": time.time()}
        self.write(response)


class CheckDB(tornado.web.RequestHandler):
    def get(self):
        response = database.execute("SELECT * FROM books WHERE isbn ='97888'").fetchall()
        self.write(str(response[0]["author"]))
