#!/bin/bash -xe

python ./manage.py dumpdata >veyepar_all.json
python ./manage.py dumpdata main >veyepar_main.json
python ./manage.py dumpdata auth.User > veyepar_all.json
