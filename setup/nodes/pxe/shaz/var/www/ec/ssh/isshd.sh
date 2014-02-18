# isshd.sh
# installs sshd in the debian installer environment
set -xe

# SHAZ=shaz.personnelware.com
SHAZ=$url

mkdir -p /var/log
touch /var/log/lastlog

anna-install openssh-server-udeb

mkdir /etc/ssh /.ssh
ssh-keygen -f /etc/ssh/ssh_host_rsa_key -t rsa -N ""
ssh-keygen -f /.ssh/rsa_key -t rsa -N ""

cd /etc/ssh
wget http://$SHAZ/ec/ssh/sshd_config

cd /.ssh
wget http://$SHAZ/ec/ssh/authorized_keys
chmod 600 authorized_keys 


# things that arn't needed now, but may come back.
# they came back.
# create an sshd user
# echo "sshd:x:0:0:installer:/:/bin/network-console" >> /etc/passwd

/usr/sbin/sshd

# show the local IP to ssh to:
ip addr show

