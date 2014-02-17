#!/bin/bash -x

cd veyepar/dj/
scp local_settings.py $1:veyepar/dj/
cd scripts
scp pw.py veyepar.cfg $1:veyepar/dj/scripts

rsync -rtvP bling $1:veyepar/dj/scripts


