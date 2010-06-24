#!/usr/bin/python

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
user_pref("capability.policy.localfilelinks.sites", "http://localhost:8080");
user_pref("capability.policy.localfilelinks.checkloaduri.enabled", "allAccess");
"""

    print "writing to", settings_path
    open(settings_path,'w').write(config)
