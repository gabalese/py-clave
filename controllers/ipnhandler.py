import tornado.web
from tornado import gen
import os
import json
from urlparse import parse_qs
import urllib2


class IpnHandler(tornado.web.RequestHandler):
    def post(self):
        with open("output.txt", "a") as f:
            paypal = 'https://www.sandbox.paypal.com/cgi-bin/webscr'
            ipn_received = self.request.body
            ipn_verify = "cmd=_notify-validate&" + ipn_received
            print ipn_verify
            req = urllib2.Request(paypal, ipn_verify)
            response = urllib2.urlopen(req)
            print response.code, response.read()
