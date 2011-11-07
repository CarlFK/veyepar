#!/bin/bash -x

rsync --files-from pull-files.txt root@shaz:/ shaz
# rsync juser@g2a:/etc/squid-deb-proxy/squid-deb-proxy.conf shaz

