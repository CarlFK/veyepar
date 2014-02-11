#!/bin/bash -x
# 
# ./cloud_sync.sh ~/Videos/veyepar/troy
# be sure not to add a trailing /

# rsync -rtvP -e 'ssh -p 222' \
rsync -rtvP  \
    --exclude="**.dv" \
    --exclude="*/tmp/*" \
    --exclude="*/bling/*" \
    -v --copy-dirlinks  \
    $1 192.237.240.167:Videos/veyepar/ 

    # $1 veyepar@nextdayvideo.com:Videos/veyepar/ 

# --bwlimit=350 
