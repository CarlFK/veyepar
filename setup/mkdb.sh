#!/bin/bash -xe

cd ../dj
python ../setup/mkdbuser.py | sudo -u postgres psql

