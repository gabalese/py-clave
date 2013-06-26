import tornado.web

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")
    
class Echo(tornado.web.RequestHandler):
    def get(self):
        self.write("I hear you, " + self.request.remote_ip)
