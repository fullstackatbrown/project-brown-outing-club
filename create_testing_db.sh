#!/bin/bash

# run w this command: bash create_testing_db.sh
# must be in the project brown outing club directory when running (for the boc_dump.sql filepath)

echo "enter your mysql password if you have it, else just press enter"
mysql -uroot -p -e "CREATE DATABASE IF NOT EXISTS boc_test;"
mysql -uroot -p boc_test < boc_dump.sql
