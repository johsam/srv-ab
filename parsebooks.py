#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import signal
import re
import datetime
import time
#import json
import argparse
import ntpath
import rarfile
import rethinkdb as r
from PIL import Image
from mutagen.mp3 import MP3

from bson import json_util
from pymongo import MongoClient

# reload(sys)
# sys.setdefaultencoding('utf8')


def log_message(message, end='\n'):
    print("{} {}".format(time.strftime("%Y-%m-%d %X"), message), end=end)
    sys.stdout.flush()


def mongo_log(author, album, narrator):
    log_message(f"Mongodb:   [insert]: '{author}:{album},{narrator}'")


def build_art_name(ab):
    return os.path.join(args.imagepath, ab['file_name'].replace('.rar', ' ' + ab['rar_albumart_size'].replace(' ', '') + '.jpg').replace(' ', '_').replace("'", ''))


def extract_art(rar_path, art_name):
    extract_path = '/tmp/audiobooks/'

    rf = rarfile.RarFile(rar_path)

    for f in rf.infolist():
        if f.isdir():
            continue

        if f.filename.endswith('AlbumArt.jpg'):

            rf.extract(f, path=extract_path)
            extracted_path = extract_path + f.filename.replace('\\', '/')
            os.rename(extracted_path, art_name)
            os.rmdir(os.path.dirname(extracted_path))
            print()
            log_message("Extracted '" + art_name + "'")


def parse_rar(path):
    # extract_path = '/tmp/audiobooks/'

    info = {'rar_files': 0,
            'rar_errors': 0,
            'rar_mp3_files': 0,
            'rar_mp3_length': 0,
            'rar_mp3_duration': '',
            'rar_mp3_album': '',
            'rar_mp3_genre': '',
            'rar_mp3_artist': '',
            'rar_other_files': 0,
            'rar_other_list': [],
            'rar_albumart': False,
            'rar_albumart_size': None
            }
    genre = []
    artist = []
    album = []
    
    print()
    log_message("Parsing '" + path + "'")

    rf = rarfile.RarFile(path)


    for f in rf.infolist():
        if f.isdir():
            continue

        info['rar_files'] = info['rar_files'] + 1

        if f.filename.endswith('AlbumArt.jpg'):
            info['rar_albumart'] = True

            with rf.open(f.filename) as aa:
                im = Image.open(aa)
                (width, height) = im.size
                info['rar_albumart_size'] = "{0} x {1}".format(width, height)
        else:
            if f.filename.endswith('.mp3'):
                info['rar_mp3_files'] = info['rar_mp3_files'] + 1

                # rf.extract(f, path=extract_path)
                # thefile = extract_path + f.filename.replace('\\', '/')

                try:

                    with rf.open(f.filename) as au:
                        audio = MP3(fileobj=au)

                    info['rar_mp3_length'] = info['rar_mp3_length'] + audio.info.length
                    if 'TCON' in audio.tags:
                        genre.append(str(audio.tags['TCON']))  # .encode('utf-8')

                    if 'TPE2' in audio.tags:
                        artist.append(str(audio.tags['TPE2']))  # .encode('utf-8')

                    if 'TALB' in audio.tags:
                        album.append(str(audio.tags['TALB']))  # .encode('utf-8')

                except:  # pylint: disable=bare-except
                    log_message("Failed to parse: '" + f.filename + "'")
                    info['rar_errors'] = info['rar_errors'] + 1

                # print f.filename.encode('utf-8'), audio.info.length
                # os.remove(thefile)

            else:
                info['rar_other_files'] = info['rar_other_files'] + 1
                bn = ntpath.basename(f.filename)
                info['rar_other_list'].append(bn)

    # Make distinct sorted

    genre = sorted(set(genre))
    artist = sorted(set(artist))
    album = sorted(set(album))

    info['rar_mp3_album'] = ",".join(album)
    info['rar_mp3_genre'] = ",".join(genre)
    info['rar_mp3_artist'] = ",".join(artist)
    info['rar_mp3_duration'] = str(datetime.timedelta(seconds=int(info['rar_mp3_length'])))

    return info


def lookup_book(author, album, narrator):
    result = r.table(args.rethinktable).filter(~r.row.has_fields('_deleted')).filter({
        'mp3_author': author,
        'mp3_album': album,
        'mp3_narrator': narrator
    }).order_by(r.asc('_item')).limit(1).run()

    if result:
        connection = client[args.mongodb_db][args.mongodb_collection]
        mongo_book = connection\
            .find_one({
                '_deleted': {"$exists": False},
                'mp3_author': author,
                'mp3_album': album,
                'mp3_narrator': narrator
            })
        # Make sure we have it in mongodb...
        if not mongo_book:
            mongo_book = result[0].copy()
            mongo_book['_rethinkdb_id'] = mongo_book.pop('id', None)
            print()
            mongo_log(mongo_book['mp3_author'], mongo_book['mp3_album'], mongo_book['mp3_narrator'])
            connection.insert(mongo_book)

        return True, result[0]

    return False, {}


def update_book(data):
    _result = r.table(args.rethinktable).filter(~r.row.has_fields('_deleted')).filter({
        'mp3_author': data['mp3_author'],
        'mp3_album': data['mp3_album'],
        'mp3_narrator': data['mp3_narrator']
    }).limit(1).delete().run()

    # Try to find the max _item key

    maxitem = 1
    try:
        # Will fail if table is empty
        maxdoc = r.table(args.rethinktable).pluck('_item').max().run()
        maxitem = maxdoc['_item'] + 1
    except:  # pylint: disable=bare-except
        pass

    data['_item'] = maxitem
    data['_lastmodified'] = int(time.time())

    mongo_book = data.copy()
    mongo_book['_rethinkdb_id'] = mongo_book.pop('id', None)

    _result = r.table(args.rethinktable).insert(data).run()

    # Now for the mongo part...

    connection = client[args.mongodb_db][args.mongodb_collection]
    connection\
        .delete_one({
            'mp3_author': mongo_book['mp3_author'],
            'mp3_album': mongo_book['mp3_album'],
            'mp3_narrator': mongo_book['mp3_narrator']
        })

    mongo_log(mongo_book['mp3_author'], mongo_book['mp3_album'], mongo_book['mp3_narrator'])
    connection.insert(mongo_book)


def parse_path(the_path):
    counter = 0
    pattern = r'(.*?)\s-\s(.*?)\s(\d+)*\s+\((.*)\)'

    for f in sorted(os.listdir(the_path)):

        counter += 1

        log_message("\rProcessing: {:04d}'".format(counter) + f + "'\x1b[0K", end='')

        if counter % 50 == 0:
            print()

        fullpath = os.path.join(the_path, f)
        st = os.stat(fullpath)
        ts = datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %T')
        data = {'_active': True, 'file_name': f, 'file_size': st.st_size,
                'file_timestamp': ts, 'file_timestamp_epoch': int(st.st_mtime)}

        mo = re.match(pattern, f, re.M | re.I)
        if mo:
            data['mp3_author'] = mo.group(1)
            data['mp3_album'] = mo.group(2)
            data['mp3_year'] = mo.group(3)
            data['mp3_narrator'] = mo.group(4)

            (found, audiobook) = lookup_book(data['mp3_author'], data['mp3_album'], data['mp3_narrator'])

            if found is True:
                if data['file_size'] == audiobook['file_size'] and data['file_timestamp_epoch'] == audiobook['file_timestamp_epoch']:
                    # log_message("Found '" + data['mp3_author'] + ':' + data['mp3_album'] + "'")
                    if audiobook['rar_albumart']:

                        art_name = build_art_name(audiobook)
                        if os.path.exists(art_name):
                            continue

                        extract_art(fullpath, art_name)
                        audiobook.update({'rar_albumart_name': os.path.basename(art_name)})

                        update_book(audiobook)

                    continue

            # Must be a new file, Read rar for info
            #import json
            #print(json.dumps(data, indent=True, sort_keys=True))
            #print(json.dumps(audiobook, indent=True, sort_keys=True))
            # sys.exit(0)

            try:
                info = parse_rar(fullpath)
                data.update(info)
                log_message("Rethinkdb: [update]: '" + f + "'")

                if data['rar_albumart']:
                    art_name = build_art_name(data)
                    if not os.path.exists(art_name):
                        extract_art(fullpath, art_name)

                    data.update({'rar_albumart_name': os.path.basename(art_name)})

                update_book(data)

            except Exception:
                log_message("Failed to parse rar: '" + f + "'")
                raise

        else:
            log_message("Failed to match: '" + f + "'")
    
    log_message("\rProcessing: {:04d}'".format(counter) + f + "'\x1b[0K", end='')


def handle_signal(_sig, _frame):
    print("Signal...")
    sys.exit(0)


def main():

    # Connect to rethinkdb
    try:
        r.connect(args.rethinkdbhost, 28015, args.rethinkdb).repl()
    except Exception as e:  # pylint: disable=broad-except
        print(e)
        sys.exit(1)

    signal.signal(signal.SIGINT, handle_signal)

    parse_path(args.path)
    print()

#
# Parse arguments
#


parser = argparse.ArgumentParser(description='Audiobook parser')

parser.add_argument(
    '--rethinkdb-host', required=True,
    default="localhost",
    dest='rethinkdbhost'
)

parser.add_argument(
    '--rethink-db', required=True,
    default="test",
    dest='rethinkdb'
)

parser.add_argument(
    '--rethink-table', required=True,
    default="test",
    dest='rethinktable'
)

parser.add_argument(
    '--mongodb-host', required=True,
    default="localhost",
    dest='mongodb_host'
)

parser.add_argument(
    '--mongodb-db', required=True,
    default="test",
    dest='mongodb_db'
)

parser.add_argument(
    '--mongodb-auth', required=True,
    default="test:test",
    dest='mongodb_auth'
)

parser.add_argument(
    '--mongodb-collection', required=True,
    default="test",
    dest='mongodb_collection'
)


parser.add_argument(
    '--path', required=True,
    default="~",
    dest='path'
)

parser.add_argument(
    '--image-path', required=False,
    default=os.path.abspath(os.path.join(os.path.dirname(__file__), 'www/albumart/')),
    dest='imagepath'
)


args = parser.parse_args()
client = MongoClient('mongodb://{}@localhost:27017'.format(args.mongodb_auth),
                     authSource=args.mongodb_db, serverSelectionTimeoutMS=5000)


if __name__ == "__main__":
    main()
