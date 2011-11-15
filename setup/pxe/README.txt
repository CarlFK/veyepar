Builds a dvswitch/veyepar node builder.

steps:

1. sudo ./install.sh
2. disconnect from primary lan
3. connect to video lan
4. ifconfig eth0 192.168.0.1
5. sudo service isc-dhcp-server start
6. hook up empty nodes, pxe boot, select "hands off install" and wait.
   takes about 20 minutes once the cache is warm.


This will install and configure all the servers, but not start dhcpd.
(you don't want a 2nd primary dhcp server on your lan.)


