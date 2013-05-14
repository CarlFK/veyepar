#!/bin/bash -xe 

target=juser@trist
target=juser@pc8

scp planet.xml default.xml $target:/tmp/
ssh $target -t \
    sudo mv /tmp/planet.xml /usr/local/etc/flumotion/managers/default/
ssh $target -t \
    sudo mv /tmp/default.xml /usr/local/etc/flumotion/workers/
