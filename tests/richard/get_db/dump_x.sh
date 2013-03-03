#!/bin/bash -xe

instance=$1

cd /srv/$instance/
source  venv/bin/activate
./manage.sh dumpdata --exclude=auth >~/richard_${instance}_all.json
./manage.sh dumpdata videos >~/richard_${instance}_videos.json

