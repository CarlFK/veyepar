#!/usr/bin/python

# makes an apache vhost config file based on settings.py 

import sys, os

from distutils.sysconfig import get_python_lib

sys.path.insert(0,'.')
import settings



# slug - the string used for user, database, config name, site name, etc.
# slug = os.path.split(settings.PROJECT_ROOT)[-1]
slug = settings.DATABASES['default']['NAME']
project_root = settings.PROJECT_ROOT
static_root = settings.STATIC_ROOT 
static_url  = settings.STATIC_URL 
site_packages = get_python_lib()

vhost = """
# /etc/apache2/sites-available/%(slug)s.conf

<VirtualHost *:80>

    ServerName %(slug)s
    ServerAlias www.%(slug)s.com %(slug)s.com

    ServerRoot /home/%(slug)s/

    CustomLog %(slug)s_access.log common
    ErrorLog %(slug)s_error.log

    # WSGIDaemonProcess %(slug)s user=%(slug)s python-path=/home/%(slug)s/.local/lib/python2.5/site-packages/
    WSGIDaemonProcess %(slug)s user=%(slug)s python-path=%(site_packages)s
    WSGIProcessGroup %(slug)s

    # Pinax 0.9a1 uses pinax.wsgi, a2 uses wsgi.py
    WSGIScriptAlias / %(project_root)s/deploy/pinax.wsgi
    # WSGIScriptAlias / %(project_root)s/deploy/wsgi.py

    Alias %(static_url)s %(static_root)s
    <Directory  %(static_root)s>
        Order deny,allow
        Allow from all
        Options FollowSymLinks Indexes SymLinksIfOwnerMatch
    </Directory>

</VirtualHost>
"""
print vhost % locals()

# add this for debugging, not for production
# http://httpd.apache.org/docs/current/mod/mod_info.html
"""
  <Location /server-info>
     SetHandler server-info
     allow from all
  </Location>
"""
