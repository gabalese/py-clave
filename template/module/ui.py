import tornado.web


class Hello(tornado.web.UIModule):
    def render(self, who):
        tmpl_str = """<p>Hello, {who}</p>
        <p>Welcome to py-clave. Proceed <a href="/catalogue">here</a> for the publication catalogue</p>
        <p>Or see <a href="http://docs.pyclave.apiary.io">here</a> for the full documentation.
        """
        return tmpl_str.format(who=who)
