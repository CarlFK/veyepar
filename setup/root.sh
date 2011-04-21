#!/bin/bash -xe

# part 1 - run as root

apt-get install --assume-yes \
 apache2 libapache2-mod-wsgi \
 postgresql python-psycopg2 \
 git-core \
 python-imaging \
 python-setuptools 

easy_install pip 
pip install virtualenv

useradd -m example --shell /bin/bash \
  --password '$1$w0VeUJmb$GPETcyAO4y.FKD7.0SD7I0'
# pw is x
mkdir /home/example/tube
cp tube/p_u.sh tube/local_settings.py /home/example/tube
chown example:example -R /home/example/tube

# Lenny apache2 install needs this to get rid of an anoying warning:
echo "ServerName foo.example.com">/etc/apache2/conf.d/foo.conf
# and disable the installed VirtualHost 
# so that apache will default to our site, 
# not the empty one that comes with Lenny
a2dissite default

cp /root/tube/example.conf /etc/apache2/sites-available
a2ensite example.conf

cp /root/tube/pg_hba.conf /etc/postgresql/8.4/main/
# /etc/init.d/postgresql-8.3 reload
service postgresql restart

su - postgres -c 'psql --command "create user example;"'
su - postgres -c 'psql --command "create database example;"'

halt

