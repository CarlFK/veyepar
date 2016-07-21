#!/bin/bash -ex

# cd veyepar/dj/
# starting where this lives
cd ../../../dj/

scp dj/local_settings.py $1:veyepar/dj/dj

cd scripts

scp \
    veyepar.cfg \
    pw.py \
    client_secrets.json oauth2-ndv.json \
    $1:veyepar/dj/scripts

rsync -rtvP bling $1:veyepar/dj/scripts/

# rsync -rtvP ~/Videos/veyepar/$client/$show/assets \
#    $1:Videos/veyepar/$client/$show/



