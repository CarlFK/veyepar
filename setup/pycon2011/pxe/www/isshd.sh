# isshd.sh
# installs sshd in the debian installer environment
set -x

mkdir -p /var/log
touch /var/log/lastlog

mkdir -p /etc/ssh
cd /etc/ssh
wget http://shaz/sshkeys.tar
tar xf sshkeys.tar
mv sshkeys/* . 
wget http://shaz/sshd_config

cd 
mkdir .ssh
cd .ssh
mv /etc/ssh/authorized_keys .

anna-install openssh-server-udeb

# things that arn't needed now, but may come back.
# they came back.
# create an sshd user
echo "sshd:x:0:0:installer:/:/bin/network-console" >> /etc/passwd

# gen host keys
# ssh-keygen -f /etc/ssh/ssh_host_rsa_key -t rsa
# wget http://shaz/authorized_keys 

/usr/sbin/sshd

# so we can see the local IP to ssh to:
ifconfig
ip addr show
