#!/bin/bash -x

time rsync -rtvP --exclude "test_client" $1.local:Videos/veyepar ~/Videos/
# rsync -rtvP --exclude "test_client" $1.local:Videos/veyepar/dv ~/Videos/veyepar/
