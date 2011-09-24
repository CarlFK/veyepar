#!/bin/bash -x

python ./manage.py dumpdata >veyepar_all.json
python ./manage.py dumpdata main >veyepar_main.json
