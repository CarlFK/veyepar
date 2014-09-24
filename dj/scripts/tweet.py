#!/usr/bin/python

# tweets #client.slug, #video, title and url
# shortens the URL and title if needed

# if over 140 char, url is shortened using bity,
# if still over, title is truncated.

import twitter

import urllib2
import urllib
import pprint

import pw  # see pw_samp.py for sample.

from process import process

# from main.models import Episode, Raw_File, Cut_List

class tweet(process):

    ready_state = 10

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

    def tweet_tweet(self, user, tweet):
        if self.options.test:
            print 'test mode:' 
            print 'user:', user
            print tweet
            ret=False
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
            self.last_tweet_url = "http://twitter.com/#!/NextDayVideo/status/{}".format(d["id"], )
            print self.last_tweet_url
            pprint.pprint(d)

            ret=True

        return ret

    def process_ep(self, ep):
        show = ep.show
        client = show.client

        # use the username for the client 
        user =  client.tweet_id

        url = ep.public_url if ep.public_url \
                else ep.host_url

        prefix = show.client.tweet_prefix

        tweet = self.mk_tweet(prefix, ep.name, ep.authors, url)

        ret=self.tweet_tweet(user, tweet)
        if ret:
            ep.twitter_url = self.last_tweet_url
            ep.save()

        return ret

    def add_more_options(self, parser):
        parser.add_option('--twitter_user',
           help="account to tweet from if not specified in client.")

    def add_more_option_defaults(self, parser):
        # lag doesn't work right now.
        # parser.set_defaults(lag=120)
        pass

if __name__ == '__main__':
    p=tweet()
    p.main()

