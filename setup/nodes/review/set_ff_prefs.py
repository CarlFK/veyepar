#!/usr/bin/python

"""
Allow a web page to access local files.
This makes it easier to preview title screens and video files.

FF stores profiles in ~/.mozilla/firefox/profiles.ini
FF settings are set by creating a .js file that sets things on startup

1. count number of FF profiles.
     If more than 1, give up.
2. get profile dir
3. create user.js that sets custom settings.
"""

import os
import ConfigParser

home_dir = os.path.expanduser('~')
print "home dir:", home_dir

profiles_path= os.path.join(home_dir, ".mozilla","firefox","profiles.ini")
print "profiles_path:", profiles_path

# read ini file
config = ConfigParser.RawConfigParser()
config.read([profiles_path])
profiles = [s for s in config.sections() if s !='General']
if len(profiles)>1:
    print "more than one profile, you fix it."
    print profiles
else:
    d=dict(config.items(profiles[0]))
    settings_path= os.path.join(home_dir, ".mozilla","firefox",d['path'],"user.js")
    config="""
user_pref("capability.policy.policynames", "localfilelinks");
user_pref("capability.policy.localfilelinks.sites", "http://localhost:8080","http://veyepar.nextdayvideo.com:8080");
user_pref("capability.policy.localfilelinks.checkloaduri.enabled", "allAccess");
"""

    print "writing to", settings_path
    open(settings_path,'w').write(config)
