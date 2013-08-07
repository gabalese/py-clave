import tornado.web


class Hello(tornado.web.UIModule):
    def render(self, who):
        return "<p>Hello, "+who+"</p>"
