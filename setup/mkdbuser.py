#!/usr/bin/env python
# mkdbuser.py
# prints the CREATE DATABASE and GRANT commands based on the local settings.py
# ./mkdbuser.py | mysql -u root -p
#  config/box/postgresql/mkdbuser.py | sudo -u postgres psql


import sys
sys.path.insert(0,'.')
import settings

# MySql
SQL = """
DROP DATABASE IF EXISTS %(db)s;
CREATE DATABASE %(db)s;
GRANT ALL
    ON %(db)s.*
    TO %(user)s
    IDENTIFIED BY '%(pw)s'
    with grant option;
"""

# PostGreSQL
SQL = """
 DROP DATABASE IF EXISTS %(NAME)s;
 DROP USER IF EXISTS %(USER)s;
 CREATE DATABASE %(NAME)s;
 CREATE USER %(USER)s WITH PASSWORD '%(PASSWORD)s';
 GRANT ALL PRIVILEGES ON DATABASE %(NAME)s TO %(USER)s;
"""

print SQL % settings.DATABASES['default']
