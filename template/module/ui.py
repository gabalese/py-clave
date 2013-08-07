import tornado.web


class Hello(tornado.web.UIModule):
    def render(self, who):
        tmpl_str = """<p>Hello, {who}</p>
        <p>Welcome to py-clave. Proceed <a href="/catalogue">here</a> for the publication catalogue</p>
        """
        return tmpl_str.format(who=who)
