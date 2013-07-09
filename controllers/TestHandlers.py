import tornado.web
import time
import json
from data.data import opendb, DBNAME


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "text/plain")
        self.render("../README.md")


class PingHandler(tornado.web.RequestHandler):
    def get(self):
        response = {"status": "200 OK", "timestamp": time.time()}
        self.write(response)


class CheckDB(tornado.web.RequestHandler):
    def get(self):
        database, conn = opendb(DBNAME)
        response = database.execute("SELECT * FROM books").fetchall()
        conn.close()
        reply = ["%s, %s, %s, %s" % (resp["isbn"],
                                     resp["author"], resp["title"], resp["path"])
                 for resp in response]
        self.set_header("Content-Type", "application/json")
        self.write(json.JSONEncoder().encode(reply))
