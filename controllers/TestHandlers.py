import tornado.web
import time
import json
import os

from data.utils import opendb


class PingHandler(tornado.web.RequestHandler):
    def get(self):
        response = {"status": "success", "timestamp": time.time()}
        self.write(response)


class CheckDB(tornado.web.RequestHandler):
    def get(self):
        database, conn = opendb()
        response = database.execute("SELECT * FROM books").fetchall()
        conn.close()
        reply = ["%s, %s, %s, %s" % (resp["isbn"],
                                     resp["author"], resp["title"], os.path.basename(resp["path"]))
                 for resp in response]
        self.set_header("Content-Type", "application/json")
        self.write(json.JSONEncoder().encode(reply))
