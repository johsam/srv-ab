#!/usr/bin/env python3

import os
import json
import logging
import signal
import time
import atexit
import pymongo
import tornado.web
import tornado.httpserver
from bson import json_util

from tornado.options import define, options
from tornado.ioloop import IOLoop
from tornado.log import LogFormatter
import motor.motor_tornado


class Application(tornado.web.Application):

    def __init__(self):

        uri = "mongodb://{}@{}:27017/?authSource={}".format(options.mongodb_auth, options.mongodb_host, options.mongodb_db)

        settings = {
            "debug": options.debug,
            "db": motor.motor_tornado.MotorClient(uri, serverSelectionTimeoutMS=5000)
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
        jsonp = "{jsfunc}({json});".format(jsfunc=callback, json=json.dumps(obj, sort_keys=True, default=json_util.default))
    else:
        jsonp = "{json}".format(json=json.dumps(obj, sort_keys=True, default=json_util.default))

    handler.set_header('Content-Type', 'application/javascript')
    handler.write(jsonp)


class ImagesHandler(tornado.web.RequestHandler):

    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    def get(self, image):  # pylint: disable=arguments-differ
        #image = urllib.parse.unquote(image)
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'albumart', image))

        try:
            with open(path, 'rb') as f:
                self.write(f.read())
                f.close()
        except BaseException:  # pylint: disable=bare-except
            self.clear()
            self.set_status(404)


# def ValidBook(book):

    # if book['rar_other_files'] == 1:
    #    return False
    # return True

    # if book['rar_albumart'] is False:
    #    return False

    # art = book['rar_albumart_size'].split('x')
    # aw = int(art[0])
    # ah = int(art[1])

    # if (aw > 500 or ah > 515):
    #    return False

    # if book['mp3_narrator'] != book['rar_mp3_artist']:
    #    return False

    # if book['rar_mp3_genre'] != 'Audiobook':
    #    return False

    # if book['rar_other_files'] > 0:
    #    return False

    # return True


class LoadHandler(tornado.web.RequestHandler):

    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    def get(self, table):  # pylint: disable=arguments-differ

        try:
            db = self.settings['db']
            connection = db[options.mongodb_db]

            list_of_collections = yield connection.list_collection_names()

            if table not in list_of_collections:
                logging.error("Bork: Collection '%s' not found in database '%s'", table, options.mongodb_db)
                self.clear()
                self.set_status(404)
                return

            collection = connection[table]
            cursor = collection\
                .find({"_deleted": {"$exists": False}})\
                .sort([("mp3_author", pymongo.ASCENDING), ("file_timestamp_epoch", pymongo.DESCENDING)])

            alldocs = []
            while (yield cursor.fetch_next):
                alldocs.append(cursor.next_object())

            result = {
                'success': True,
                'rows': alldocs,
                'totalcount': len(alldocs),
                'rowcount': len(alldocs)
            }

            replyWithJsonP(self, result)

        except json.JSONDecodeError as e:
            self.clear()
            self.set_status(500)
            logging.error("JSONDecodeError: Something went wrong, '%s'", str(e))

        except pymongo.errors.PyMongoError as e:
            self.clear()
            self.set_status(500)
            logging.error("PyMongoError: Something went wrong, '%s'", str(e))

        except Exception as e:
            self.clear()
            self.set_status(500)
            logging.error("Exception: Something went wrong, '%s'", str(e))


class IndexHandler(tornado.web.RequestHandler):

    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    def get(self):  # pylint: disable=arguments-differ
        try:
            with open('index.html') as f:
                self.write(f.read())
            f.close()
        except FileNotFoundError as e:
            self.clear()
            self.set_status(404)
            logging.error("Exception: Something went wrong, '%s'", str(e))


#
# Handle signals
#


def shutdownHandler():
    logging.warning("Shutting down...")
    time.sleep(1)
    ioloop.stop()


def main():

    define("port", default=7788, help="bind to this port", type=int)
    define("listen", default="127.0.0.1", help="listen address", type=str)
    define("debug", default=False, help="debug", type=bool)
    define("mongodb_host", default="mongo", help="mongo hostname", type=str)
    define("mongodb_db", default="test", help="mongo default database", type=str)
    define("mongodb_auth", default="user:user", help="mongo auth user", type=str)

    tornado.options.parse_command_line()

    applicaton = Application()
    http_server = tornado.httpserver.HTTPServer(applicaton, xheaders=True)
    http_server.listen(options.port, address=options.listen)

    # Setup signal handlers
    signal.signal(signal.SIGINT, lambda sig, frame: ioloop.add_callback_from_signal(exit))
    signal.signal(signal.SIGTERM, lambda sig, frame: ioloop.add_callback_from_signal(exit))
    atexit.register(shutdownHandler)

    # Setup logging
    my_log_format = '%(color)s%(asctime)s %(levelname)1.1s [%(module)s:%(lineno)d]%(end_color)s %(message)s'
    my_log_formatter = LogFormatter(fmt=my_log_format, datefmt='%Y-%m-%d %H:%H:%S', color=False)

    for handler in logging.getLogger().handlers:
        handler.setFormatter(my_log_formatter)

    # Fire up our server

    logging.info('Server started on %s:%d', options.listen, options.port)

    ioloop.start()


if __name__ == "__main__":
    ioloop = IOLoop.instance()
    main()
