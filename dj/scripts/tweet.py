#!/usr/bin/python

# tweets #client.slug, #video, title and blipurl
# shortens the URL and title if needed

# if over 140 char, url is shortened using bity,
# if still over, title is truncated.

import twitter

import urllib2
import urllib
import time

import pw  # see pw_samp.py for sample.

from process import process

# from main.models import Episode, Raw_File, Cut_List

class tweet(process):

    ready_state = 5

    def shorten(self, url):
        return url # hack because auth broke:
        ## Out[15]: '{\n    "errorCode": 203, \n    "errorMessage": "You must be authenticated to access shorten", \n    "statusCode": "ERROR"\n}'

        d=dict(version='2.0.1',login=pw.bitly['user'], apikey=pw.bitly['password'], longurl=url)
        q = urllib.urlencode(d)
        print q
        url = 'http://api.bit.ly/shorten?' + q
        data = eval(urllib2.urlopen(url).read())
        print data
        return data['results'].values()[0]['shorturl']

    def mk_tweet(self, prefix, video_name, authors, video_url):
        message = ' '.join([prefix, video_name, '-', authors, video_url])
        if len(message) > 140:
            message = ' '.join([prefix, video_name, video_url])
        if len(message) > 140:
            short_url = self.shorten(video_url)
            message = ' '.join([prefix, video_name, short_url])
        if len(message) > 140:
            video_name = video_name[:140 - len(message) - 3] + '...'
            message = ' '.join([prefix, video_name, short_url])
        return message

    def process_ep(self, ep):
        if self.options.verbose: print ep.id, ep.name
        show = ep.show
        client = show.client

        # use the username for the client, else use the first user in pw.py
        user =  client.blip_user if client.blip_user else 'nextdayvideo'

        blip_url="http://%s.blip.tv/file/%s" % (user,ep.target)
        prefix = "#%s #VIDEO" % show.client.slug
        tweet = self.mk_tweet(prefix, ep.name, ep.authors, blip_url)

        ret=False
        if self.options.test:
            print 'test mode:', tweet
        else:
            print 'tweeting:', tweet
            # print user,password
            t = pw.twit[user]
            api = twitter.Api(consumer_key=t['consumer_key'], 
                     consumer_secret=t['consumer_secret'],
                     access_token_key=t['access_key'], 
                     access_token_secret=t['access_secret'] )
            if self.options.verbose: print api.VerifyCredentials()
            status = api.PostUpdate(tweet)
            d=status.AsDict()
            self.last_tweet = d
            ret=True

        return ret

if __name__ == '__main__':
    p=tweet()
    p.main()

