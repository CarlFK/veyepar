#!/bin/sh

# Seperated into a different file to stop NFS issues halting entire loop

. /scripts/A-config.sh
echo Remounting NFS share and starting NFS sink...
echo Errors here are OK - NFS is not a crucial part of this AV loop

sudo mount $NFSDV

mkdir $NFSDV/$ROOMNAME 2> /dev/null
mkdir $NFSDV/$ROOMNAME/$DATE 2> /dev/null
dvsink-files -h $DVHOST -p $DVPORT $NFSDV/$ROOMNAME/$DATE/%T.dv

