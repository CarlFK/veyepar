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

    ready_state = 4

    def post_to_twitter(message):
        cmd = ['curl', '-u', '%s:%s'%(pw.twit['user'], pw.twit['password']), '-d', 'status="%s"'%message, 'http://twitter.com/statuses/update.xml']
        print cmd
        p = subprocess.popen(cmd, stdout=subprocess.pipe, stderr=subprocess.pipe )
        p.wait()
        out,err = p.communicate()
        print 'e', err
        return out

    def shorten(url):
        d=dict(version='2.0.1',login=pw.bitly['user'], apikey=pw.bitly['password'], longurl=url)
        q = urllib.urlencode(d)
        print q
        url = 'http://api.bit.ly/shorten?' + q
        data = eval(urllib2.urlopen(url).read())
        print data
        return data['results'].values()[0]['shorturl']

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

    def process_ep(self, ep):
        print ep.id, ep.name
        loc = ep.location
        show = loc.show
        client = show.client

        video_id = ep.comment.strip(' \n')[-7:]
        print ep.name, video_id

        ret=False
        if self.options.test:
            print 'test mode:'
            print '( video_id, user, pw)'
            print video_id, pw.twit['user'], pw.twit['password']
            print
        
        else:
            print blipurl
            prefix = "%s #VIDEO -" % show.client.slug
            tweet = tweeter.notify(prefix, ep.name, blipurl)
            print tweet
            if "<id>" not in tweet: print tweet
            tweetid=re.search("<id>(.*)</id>" ,tweet).groups()[0]
            tweeturl="http://twitter.com/cfkarsten/status/%s"%(tweetid,)
            print tweeturl
            ret=True
            ep.save()

        return ret

if __name__ == '__main__':
    p=tweet()
    p.main()

