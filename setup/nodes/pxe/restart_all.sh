#!/bin/bash -x

sudo service isc-dhcp-server stop
sudo service bind9 stop
sudo service squid-deb-proxy stop

sudo service isc-dhcp-server start
sudo service bind9 start
sudo service squid-deb-proxy start
