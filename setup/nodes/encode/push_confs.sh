#!/bin/bash -x

# cd veyepar/dj/
cd ../../../dj/

scp local_settings.py $1:veyepar/dj/
cd scripts
scp pw.py veyepar.cfg \
    client_secrets.json oauth2-ndv.json \
    $1:veyepar/dj/scripts

source veyepar.cfg
rsync -rtvP bling/$client $1:veyepar/dj/scripts/bling


rsync -rtvP ~/Videos/veyepar/$client/$show/assets \
   $1:Videos/veyepar/$client/$show/



