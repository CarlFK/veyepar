#!/bin/bash -xe 

target=juser@trist
# scp planet.xml juser@cnt2:/usr/local/etc/flumotion/managers/default/
scp planet.xml default.xml $target:/tmp/
ssh $target -t \
    sudo mv /tmp/planet.xml /usr/local/etc/flumotion/managers/default/
ssh $target -t \
    sudo mv /tmp/default.xml /usr/local/etc/flumotion/workers/
