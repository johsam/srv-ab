#!/bin/bash

. /etc/default/audiobooks

./parsebooks.py \
    --rethinkdb-host localhost \
    --rethink-db=${rethinkdb_db} \
    --rethink-table=${rethinkdb_table} \
    --path=${path} | tee -a ab.log
