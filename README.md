py-clave
========

A prototype server implementation of a **set of public RESTful APIs** meant to enable clients to **retrieve metadata and contents** from a bunch of digital publications in **[EPUB2](http://idpf.org/epub/201) format** stored in free-form directory structure.

Written in [Python](http://www.python.org), it is built on the [tornado](http://www.tornadoweb.org/en/stable/) framework, an asynchronous non-blocking web library tuned for high performance and scalability.

The core application in [/server.py](https://github.com/gabalese/py-clave/blob/master/server.py) implements the tornado.web.Application class, with asynchronous handlers for each endpoint. It is meant to be deployed with [supervisord](http://supervisord.org/) process control system, in multiple instances listening to different ports, behind a [nginx](http://nginx.org/) frontend acting as a reversed proxy. The main process is run on the default 8080 port.

On first run and after a fixed amount of time the server builds a sqlite3 cache of EPUB files stored in the `EPUB_FILES_PATH` directory (set at startime with the `--EPUB_FILES_PATH` flag) in order to avoid filesystem traversal on each request. The cache is then updated with a [periodic callback](http://www.tornadoweb.org/en/stable/ioloop.html#tornado.ioloop.PeriodicCallback) invoked with a default interval of 5m, or an interval provided by `--DB_UPDATE_TIMEOUT` flag.

Exhaustive documentation for the implemented HTTP request may be found on the official [DOCS](http://docs.pyclave.apiary.io/). The API is currently designed to differentiate between a GET request coming from a browser reading the `Accept`: request header, thus showing a descriptive UI rather than raw JSON output.

Installation
------------

Just `clone` the master tree.

```bash
$ git clone https://github.com/gabalese/py-clave.git
$ cd py-clave
```

Usage
-----

The server is started by executing the `server.py` file:

```bash
$ python server.py &
```

Which starts the server with its default configuration (listening on port 8080).

User interface
--------------

py-clave now supports a browser interaction. Opening `http://localhost:8080` with a browser shows the welcome page, with a link to `http://localhost:8080/catalogue`, which renders the catalogue template.

Every relevant endpoint returns a JSON object when the HTTP request doesn't include `text/html` in the `Accept:` header.

Configuration
-------------

py-clave now supports tornado.options. To overwrite defaults, add a supported --FLAG=value when starting `server.py`. The following command shows all the supported parameters.

```bash
$ python server.py --PORT=8081 --EPUB_FILES_PATH=/absolute/path/to/files/directory --DBNAME=name.sql \
--DB_UPDATE_TIMEOUT=100000 --FEED_UPDATE_TIMEOUT=300000 &
```

`--PORT` (int): the port on which the server will keep listening

`--EPUB_FILES_PATH` (str): the absolute path where the epub files are stored

`--DBNAME` (str): name of the sqlite cache file

`--DB_UPDATE_TIMEOUT` (milliseconds): interval between DB updates

Version 1.1 integrated database and feed update routines, so `--FEED_UPDATE_TIMEOUT` is no more supported.

The intended deployement scenario involves more than one tornado instances on the same server, behind a nginx frontend. Different instances can *in theory* accept different `--EPUB_FILES_PATH` strings, but the `--DBNAME` must be the same or inconsistency may arise unnoticed (since every instance is executed in a different process).

License
-------

The source code is provided as-is under the MIT License.

TL;DR? Do whatever you wish with it, but keep the original attribution.

Contribute
----------

Suggestions, pull requests, issues and NOS feedback are welcome. The present code shows a few weakness, in particular the database access abstraction (or the lack of one) and could be extended in many ways, for example user authentication. Also, the EPUB class might be extended to comply with richer EPUB3 metadata.
