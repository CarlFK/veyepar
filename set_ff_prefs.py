#!/usr/bin/python

import os
import ConfigParser

home_dir = os.path.expanduser('~')
profile_path= os.path.join(home_dir, ".mozilla","firefox","profiles.ini")
config = ConfigParser.RawConfigParser()
files=config.read([profile_path])
d=dict(config.items('Profile0'))
profile_path= os.path.join(home_dir, ".mozilla","firefox",d['path'],"user.js")
config="""
user_pref("capability.policy.policynames", "localfilelinks");
user_pref("capability.policy.localfilelinks.sites", "http://localhost:8080");
user_pref("capability.policy.localfilelinks.checkloaduri.enabled", "allAccess");
"""

print "writing to", profile_path

open(profile_path,'w').write(config)
