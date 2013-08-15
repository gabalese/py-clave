import os

from tornado.options import options
from tornado.options import define


dbname = os.path.join(os.path.dirname(__file__), os.pardir, "base.sql")
epub_path = os.path.join(os.path.dirname(__file__), os.pardir, "files")

define("DBNAME", default=dbname, help="Name of the local DB cache")
define("PORT", default=8080, help="Port to listen to")
define("DB_UPDATE_TIMEOUT", default=1000000, help="Interval to update DB")
define("EPUB_FILES_PATH", default=epub_path, help="Files storage directory")

if os.path.exists(os.path.join(__file__, os.pardir, "config.conf")):
    options.parse_config_file(os.path.join(__file__, os.pardir, "config.conf"))
else:
    options.parse_command_line()

for i in options.items():
    print "{} = {}".format(i[0], i[1])

EPUB_FILES_PATH = options.EPUB_FILES_PATH
DBNAME = os.path.join(os.path.dirname(__file__), os.pardir, options.DBNAME)
PORT, DB_UPDATE_TIMEOUT = options.PORT, options.DB_UPDATE_TIMEOUT
