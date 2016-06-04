#!/bin/bash -x

time rsync -rtvP --exclude "test_client" $1.local:Videos/veyepar ~/Videos/
# time rsync -rtvP --bwlimit=3500 --exclude "test_client" $1.local:Videos/veyepar ~/Videos/
#   4,499,009,440  92%    3.50MB/s    0:01:43  

# rsync -rtvP --exclude "test_client" $1.local:Videos/veyepar/dv ~/Videos/veyepar/
