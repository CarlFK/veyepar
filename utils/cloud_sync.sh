#!/bin/bash -x
# 
# ./cloud_sync.sh ~/Videos/veyepar/troy
# be sure not to add a trailing /

rsync -rtvP -e 'ssh -p 222' \
    --exclude="**.dv" \
    --exclude="*/tmp/*" \
    --exclude="*/bling/*" \
    -v --copy-dirlinks  \
    $1 veyepar@nextdayvideo.com:Videos/veyepar/ 

# --bwlimit=350 
