#!/bin/sh

# Seperated into a different file to stop NFS issues halting entire loop

. /scripts/A-config.sh

echo Remounting NFS share and starting NFS sink...
echo Errors here are OK - NFS is not a crucial part of this AV loop

mount $NFSDV

dvsink-files $NFSDV/$ROOMNAME/%Y-%m-%d/%H_%M_%S.dv

