#!/usr/bin/python
import subprocess
import urllib2
import urllib

# TWITTER_USERNAME = 'offbytwo'
# TWITTER_PASSWORD = 'iamc05m1n'

TWITTER_USERNAME = 'cfkarsten'
TWITTER_PASSWORD = 'netsrak1'

BITLY_USERNAME = 'cstejerean'
BITLY_API_KEY = 'R_d2f2c394e54016d37bd8b340eebffe2a'

def post_to_twitter(message):
    cmd = ('curl -u %s:%s -d status="%s" http://twitter.com/statuses/update.xml' % ( TWITTER_USERNAME, TWITTER_PASSWORD, message)).split()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
    p.wait()
    out,err = p.communicate()
    return out

def shorten(url):
    q = urllib.urlencode(dict(version='2.0.1',login=BITLY_USERNAME, apiKey=BITLY_API_KEY, longUrl=url))
    url = 'http://api.bit.ly/shorten?' + q
    data = eval(urllib2.urlopen(url).read())
    return data['results'].values()[0]['shortUrl']

def notify(prefix, video_name, video_url):
    short_url = shorten(video_url)
    max_video_len = 140 - len(' from @' + TWITTER_USERNAME) - len(prefix) - len(short_url)
    if len(video_name) > max_video_len:
        video_name = video_name[:max_video_len - 3] + '...'
    message = ' '.join([prefix, video_name, short_url])
    ret = post_to_twitter(message)
    print ret
    return ret
