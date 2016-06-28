# To deploy webserver and database to a remote box:

fabfile.py
  'hosts': ['root@104.130.73.49'],

# set up ssh keys

fab prod provision

# do things fabfile.py didn't do for us.
ssh root@104.130.73.49

# set postgresql to listen on all ports
sudo vim  /etc/postgresql/9.4/main/postgresql.conf 

#listen_addresses = 'localhost' 
listen_addresses = '*'

# allow connections from known IPs
sudo vim  /etc/postgresql/9.4/main/pg_hba.conf

# vagrant host:
host    veyepar      veyepar      10.0.2.2/32       md5

# restart server to read above conf changes
sudo service postgresql restart

# set dataase server password
sudo su - postgres
psql
alter USER veyepar WITH PASSWORD 'pass123';

# create a django admin:
sudo su - veyepar
source venvs/veyepar/bin/activate
cd site/veyepar/dj/
./manage.py createsuperuser
# then enter a user, bogus email and password

local scripts dir:
veyepar.cfg

client=debian
show=debconf15
schedule=https://summit.debconf.org/debconf15.xml

../dj/local_settings.py

  6  'HOST': '104.130.73.49',
 10  'PASSWORD': 'pass123',

