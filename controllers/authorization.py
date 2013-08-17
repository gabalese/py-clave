import base64
import functools


def httpbasic(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        auth_header = self.request.headers.get('Authorization')
        if auth_header is None or not auth_header.startswith('Basic '):
            self.set_status(401)
            self.set_header('WWW-Authenticate', 'Basic realm=Restricted')
            self._transforms = []
            self.finish()
            return None
        else:
            auth_decoded = base64.decodestring(auth_header[6:])
            username, password = auth_decoded.split(':', 2)
            kwargs['user'], kwargs['pass'] = username, password
            return method(self, *args, **kwargs)
    return wrapper
