Builds a dvswitch/veyepar node builder.

steps:

1. sudo ./install.sh
2. disconnect from primary lan
3. connect to video lan
4. ifconfig eth0 192.168.0.1
4.1 until this gets fixed: 
    debian-installer "installer stops using proxy" 
    https://launchpad.net/bugs/889656
4.1 connect 2nd interface to internet (wifi, phone, whatever)
4.2 nmake sure it does not have a 192.168.0.x IP 
      (given that is very likely, this should be changed.)
4.2 sudo ./nat.sh 
5. sudo service isc-dhcp-server start
6. hook up empty nodes, pxe boot, select "hands off install" and wait.
   takes about 20 minutes once the cache is warm.


This will install and configure all the servers, but not start dhcpd.
(you don't want a 2nd primary dhcp server on your lan.)


