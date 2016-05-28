Builds a dvswitch/veyepar node builder.

steps:

1. start with a vanallia Ubuntu box.
2. sudo apt-get install git-core
3. git clone git://github.com/CarlFK/veyepar.git
4. cd veyepar/setup/nodes/pxe
5. sudo ./install.sh

This will install and configure all the servers, but not start dhcpd.
(you don't want a 2nd primary dhcp server on your lan.)

6. disconnect from primary lan
7. connect to video lan
8. ifconfig eth0 192.168.0.1
9. sudo service isc-dhcp-server start
10. hook up empty nodes, pxe boot, select "hands off install" and wait.
   takes about 20 minutes once the cache is warm.



