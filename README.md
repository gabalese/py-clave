py-clave
========

A prototype implementation of a **set of public RESTful APIs** meant to enable clients to **retrieve metadata and contents** from a bunch of digital publications in **[EPUB2](http://idpf.org/epub/201) format** stored in free-form directory structure.

Written in [Python](http://www.python.org), it is built on the [tornado](http://www.tornadoweb.org/en/stable/) framework, an asynchronous non-blocking web library tuned for high performance and scalability.

The core application in [/server.py](https://github.com/gabalese/py-clave/blob/master/server.py) implements the tornado.web.Application class, with threaded asynchronous handlers for each endpoint. It is meant to be deployed with [supervisord](http://supervisord.org/) process control system, in multiple instances listening to different ports, behind a [nginx](http://nginx.org/) frontend acting as a reversed proxy. The main process is run on the default 8080 port.

On first run and after a fixed amount of time the server builds a sqlite3 cache of EPUB files stored in the `EPUB_FILES_PATH` directory (set in [data.py](https://github.com/gabalese/py-clave/blob/master/data/data.py)) in order to avoid filesystem traversal on each request. The cache is then updated with a [periodic callback](http://www.tornadoweb.org/en/stable/ioloop.html#tornado.ioloop.PeriodicCallback) invoked with a default interval of 120s, or an interval provided by CLI argument.

Exhaustive documentation for the implemented HTTP request may be found on the official [DOCS](http://docs.pyclave.apiary.io/). The API is currently designed to differentiate between a GET request coming from a browser reading the `Accept`: request header.

License
-------

The source code is provided as-is under the MIT License.

TL;DR? Do whatever you wish with it, but keep the original attribution.

Contribute
----------

Suggestions, pull requests, issues and NOS feedback are welcome. The present code shows a few weakness, in particular the database access abstraction (or the lack of one) and could be extended in many ways, for example user authentication. Also, the EPUB class might be extended to comply with richer EPUB3 metadata.
