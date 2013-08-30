import base64
import functools


def httpbasic(method):
    """
    Thanks Kevin Kelley <kelleyk@kelleyk.net> 2011
    http://kelleyk.com/post/7362319243/easy-basic-http-authentication-with-tornado
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        auth_header = self.request.headers.get('Authorization')
        if auth_header is None or not auth_header.startswith('Basic '):
            self.set_status(401)
            self.set_header('WWW-Authenticate', 'Basic realm=Restricted')
            self.finish()
            return None
        else:
            auth_decoded = base64.decodestring(auth_header[6:])
            username, password = auth_decoded.split(':', 2)
            kwargs['user'], kwargs['pass'] = username, password
            return method(self, *args, **kwargs)
    return wrapper


def unauthorized(method):
    """
    Temporary decorator to disable access to endpoints
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        self.set_status(403)
        self.write("Unavailable")
        self.finish()
        return None
    return wrapper
