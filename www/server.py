import os
import json
import logging
import signal
import sys
import time
import atexit
import tornado.web
import tornado.httpserver
from tornado.options import define, options
from tornado.escape import json_encode
from tornado.ioloop import IOLoop
from tornado.options import options
import rethinkdb as r


class Application(tornado.web.Application):

    def __init__(self):

        settings = {
            "debug": options.debug,
        }

        handlers = [
            (r"/audiobooks/load/(.*)", LoadHandler),
            (r"/audiobooks/images/(.*)", ImagesHandler),
            (r"/audiobooks/assets/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "assets")}),
            (r"/(?:[^/]*)/?", IndexHandler),
        ]

        tornado.web.Application.__init__(self, handlers, **settings)


def replyWithJsonP(handler, obj):
    callback = handler.get_argument('callback', default='')
    if callback != '':
        jsonp = "{jsfunc}({json});".format(jsfunc=callback, json=json_encode(obj, sort_keys=True))
    else:
        jsonp = "{json}".format(json=json_encode(obj))

    handler.set_header('Content-Type', 'application/javascript')
    handler.write(jsonp)


class ImagesHandler(tornado.web.RequestHandler):

    @tornado.gen.coroutine
    def get(self, image):
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'albumart', image))
        try:
            with open(path) as f:
                self.write(f.read())
                f.close()
        except:
            self.clear()
            self.set_status(404)
            pass


def ValidBook(book):

    if book['rar_other_files'] == 1:
        return False
    return True

    if book['rar_albumart'] is False:
        return False

    # art = book['rar_albumart_size'].split('x')
    # aw = int(art[0])
    # ah = int(art[1])

    # if (aw > 500 or ah > 515):
    #    return False

    if book['mp3_narrator'] != book['rar_mp3_artist']:
        return False

    if book['rar_mp3_genre'] != 'Audiobook':
        return False

    if book['rar_other_files'] > 0:
        return False

    return True


class LoadHandler(tornado.web.RequestHandler):

    @tornado.gen.coroutine
    def get(self, table):
        try:
            conn = yield r.connect(options.rethinkdb_host, 28015, options.rethinkdb_db)

            orderList = [r.desc('mp3_author'), '_item']

            alldocs = yield r.table(table).filter(~r.row.has_fields('_deleted')).order_by(*orderList).limit(10000).run(conn)

            # alldocs[:] = [x for x in alldocs if not ValidBook(x)]

            result = {
                'suscess': True,
                'rows': alldocs,
                'totalcount': len(alldocs),
                'rowcount': len(alldocs)
            }
            replyWithJsonP(self, result)

        except:
            self.clear()
            self.set_status(404)
            raise

        finally:
            yield conn.close()


class IndexHandler(tornado.web.RequestHandler):

    @tornado.gen.coroutine
    def get(self):
        with open('index.html') as f:
            self.write(f.read())
        f.close()


#
# Handle signals
#


def shutdownHandler():
    logging.warning("Shutting down...")
    time.sleep(1)
    ioloop.stop()


def main():

    define("port", default=8080, help="bind to this port", type=int)
    define("listen", default="127.0.0.1", help="listen address", type=str)
    define("debug", default=False, help="debug", type=bool)
    define("rethinkdb_host", default="localhost", help="rethinkdb hostname", type=str)
    define("rethinkdb_db", default="", help="rethinkdb default database", type=str)
    define("log_file_prefix", default="/var/log/audiobooks.log", help="log file prefix")

    tornado.options.parse_command_line()

    applicaton = Application()
    http_server = tornado.httpserver.HTTPServer(applicaton, xheaders=True)
    http_server.listen(options.port, address=options.listen)

    # Setup signal handlers
    signal.signal(signal.SIGINT, lambda sig, frame: ioloop.add_callback_from_signal(exit))
    signal.signal(signal.SIGTERM, lambda sig, frame: ioloop.add_callback_from_signal(exit))
    atexit.register(shutdownHandler)

    try:
        conn = r.connect(options.rethinkdb_host, 28015, options.rethinkdb_db)
    except:
        logging.error("Could not connect to rethinkdb on host '%s'", options.rethinkdb_host, exc_info=False)
        sys.exit(1)

    # Fire up our server

    r.set_loop_type("tornado")
    ioloop.start()

if __name__ == "__main__":
    ioloop = IOLoop.instance()
    main()
