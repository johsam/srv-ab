#!/bin/bash

. /etc/default/audiobooks

./parsebooks.py \
    --rethinkdb-host localhost \
    --rethink-db=${rethinkdb_db} \
    --rethink-table=${rethinkdb_table} \
    --mongodb-host=${mongodb_host} \
    --mongodb-db=${mongodb_db} \
    --mongodb-auth=${mongodb_auth} \
    --mongodb-collection=${mongodb_collection} \
    --path=${path} | tee -a ab.log
