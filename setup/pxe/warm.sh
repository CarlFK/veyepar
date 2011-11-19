#!/bin/bash -xe

# awk '{print $7}' /var/log/squid-deb-proxy/access.log > oneiric64.urls
http_proxy=192.168.0.1:8000 wget -i oneiric64.urls -O /dev/null
exit
# ssh-copy-id juser@$1
ssh juser@$1 mkdir -p pxe
rsync -rtvP install.sh nat.sh shaz juser@$1:pxe
# ssh juser@$1 "cd pxe;./pull.sh"
# rsync -rtvopP pc8:/var/cache/squid-deb-proxy /var/cache
# sudo rsync -rtvopP /var/cache/squid-deb-proxy 192.168.0.10:/var/cache
# sudo rsync -rtvopP 192.168.0.1:/var/cache/squid-deb-proxy /var/cache
git clone git://github.com/CarlFK/veyepar.git

