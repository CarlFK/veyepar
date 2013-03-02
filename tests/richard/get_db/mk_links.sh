#!/bin/bash -x 

SRC_DIR=${0%/*}

ln -s $SRC_DIR/auth.json 
ln -s $SRC_DIR/reset_db.sh 
ln -s $SRC_DIR/runsrv.sh 

