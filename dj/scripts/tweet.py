#!/usr/bin/python

# tweets #client.slug, #video, title and blipurl
# shortens the URL and title if needed

# if over 140 char, url is shortened using bity,
# if still over, title is truncated.

import twitter

import urllib2
import urllib
import pw  # see pw_samp.py for sample.

from process import process

# from main.models import Episode, Raw_File, Cut_List

class tweet(process):

    ready_state = 5

    def post_to_twitter(message):
        cmd = ['curl', '-u', '%s:%s'%(pw.twit['user'], pw.twit['password']), '-d', 'status="%s"'%message, 'http://twitter.com/statuses/update.xml']
        print cmd
        p = subprocess.popen(cmd, stdout=subprocess.pipe, stderr=subprocess.pipe )
        p.wait()
        out,err = p.communicate()
        print 'e', err
        return out

    def shorten(self, url):
        d=dict(version='2.0.1',login=pw.bitly['user'], apikey=pw.bitly['password'], longurl=url)
        q = urllib.urlencode(d)
        print q
        url = 'http://api.bit.ly/shorten?' + q
        data = eval(urllib2.urlopen(url).read())
        print data
        return data['results'].values()[0]['shorturl']

    def mk_tweet(self, prefix, video_name, video_url):
        message = ' '.join([prefix, video_name, video_url])
        if len(message) > 140:
            short_url = self.shorten(video_url)
            message = ' '.join([prefix, video_name, short_url])
        if len(message) > 140:
            video_name = video_name[:140 - len(message) - 3] + '...'
            message = ' '.join([prefix, video_name, short_url])
        return message

    def process_ep(self, ep):
        print ep.id, ep.name
        loc = ep.location
        show = loc.show
        client = show.client

        blip_url="http://carlfk.blip.tv/file/%s" % ep.target
        prefix = "#%s #VIDEO" % show.client.slug
        tweet = self.mk_tweet(prefix, ep.name, blip_url)

        ret=False
        if self.options.test:
            print 'test mode:'
            print 'prefix, ep.name, blip_url'
            print 1, prefix, ep.name, blip_url
            print 2, tweet
            print
        else:
            api = twitter.Api(
                username=pw.twit['user'], password=pw.twit['password'])
            # print 1, api.AsDict()
            status = api.PostUpdate(tweet)
            d=status.AsDict()
            print 2, d
            ret=True
            self.log_info(d.__str__())

        return ret

if __name__ == '__main__':
    p=tweet()
    p.main()

