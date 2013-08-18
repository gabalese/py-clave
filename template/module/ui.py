import tornado.web


class Hello(tornado.web.UIModule):
    def render(self, who):
        tmpl_str = """<h4>Hello, {who}!</h4>
        """
        return tmpl_str.format(who=who)
