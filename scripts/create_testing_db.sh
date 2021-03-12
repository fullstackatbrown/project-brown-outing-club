#!/bin/bash

# run w this command: bash create_testing_db.sh
# must be in the project brown outing club directory when running (for the boc_dump.sql filepath)

sudo mysql -uroot -e "CREATE DATABASE IF NOT EXISTS boc_test; GRANT ALL PRIVILEGES ON *.* TO 'tester'@'localhost' IDENTIFIED BY 'password';"
sudo mysql -uroot boc < boc_dump.sql
