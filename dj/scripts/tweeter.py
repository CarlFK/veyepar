#!/usr/bin/python

# tweets prefix - title url
# veyepar does: "#client VIDEO -" <episode title> <url>
# if over 140 char, url is shortened using bity,
# if still over, title is truncated.
# TODO: pass in account name/pw

import subprocess
import urllib2
import urllib
import pw  # see pw_samp.py for sample.

def post_to_twitter(message):
    cmd = ['curl', '-u', '%s:%s'%(pw.twit['user'], pw.twit['password']), '-d', 'status="%s"'%message, 'http://twitter.com/statuses/update.xml']
    print cmd
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
    p.wait()
    out,err = p.communicate()
    print 'e', err
    return out

def shorten(url):
    d=dict(version='2.0.1',login=pw.bitly['user'], apiKey=pw.bitly['password'], longUrl=url)
    q = urllib.urlencode(d)
    print q
    url = 'http://api.bit.ly/shorten?' + q
    data = eval(urllib2.urlopen(url).read())
    print data
    return data['results'].values()[0]['shortUrl']

def notify(prefix, video_name, video_url):
    message = ' '.join([prefix, video_name, video_url])
    if len(message) > 140:
        short_url = shorten(video_url)
        message = ' '.join([prefix, video_name, short_url])
    if len(message) > 140:
        video_name = video_name[:140 - len(message) - 3] + '...'
        message = ' '.join([prefix, video_name, short_url])
    ret = post_to_twitter(message)
    return ret
