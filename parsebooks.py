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


# reload(sys)
# sys.setdefaultencoding('utf8')


def log_message(message):
    print("{} {}".format(time.strftime("%Y-%m-%d %X"), message))
    sys.stdout.flush()


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

            log_message("Extracted '" + art_name + "'")


def parse_rar(path):
    # extract_path = '/tmp/audiobooks/'

    info = {'rar_files': 0,
            'rar_errors': 0,
            'rar_mp3_files': 0,
            'rar_mp3_length': 0,
            'rar_mp3_duration': '',
            'rar_mp3_genre': '',
            'rar_mp3_artist': '',
            'rar_other_files': 0,
            'rar_other_list': [],
            'rar_albumart': False,
            'rar_albumart_size': None
            }
    genre = []
    artist = []

    rf = rarfile.RarFile(path)

    log_message("Parsing '" + path + "'")

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
        return True, result[0]
    else:
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

    _result = r.table(args.rethinktable).insert(data).run()


def parse_path(the_path):

    _file_list = []
    pattern = r'(.*?)\s-\s(.*?)\s(\d+)*\s+\((.*)\)'

    for f in sorted(os.listdir(the_path)):
        # if len(file_list) >= 30:
        #    break

        # log_message("Processing: '" + f + "'")

        fullpath = os.path.join(the_path, f)
        st = os.stat(fullpath)
        ts = datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %T')
        data = {'_active': True, 'file_name': f, 'file_size': st.st_size, 'file_timestamp': ts, 'file_timestamp_epoch': int(st.st_mtime)}

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
                log_message("Updating: '" + f + "'")

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
    default="ripan",
    dest='rethinkdb'
)

parser.add_argument(
    '--rethink-table', required=True,
    default="test",
    dest='rethinktable'
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


if __name__ == "__main__":
    main()
