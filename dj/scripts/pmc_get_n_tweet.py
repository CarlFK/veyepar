#!/usr/bin/python

# looks to pmc rss to see if it is ready
# grabs the pmc URL, stores it, calls tweet.

"""
feed = feedparser.parse('http://python.mirocommunity.org/feeds/category/pyohio-2011')
>>> [ (fe['link'], [ l['href'] for l in fe['links'] if l['rel']=='via' ][0]) for fe in feed['entries'] ]
[(u'http://python.mirocommunity.org/video/4373/pyohio-2011-data-transfer-obje', u'http://blip.tv/file/5419876'), (u'http://python.mirocommunity.org/video/4372/pyohio-2011-using-fabric-from-', u'http://blip.tv/file/5419406'), (u'http://python.mirocommunity.org/video/4371/pyohio-2011-aspen-a-next-gener', u'http://blip.tv/file/5419329')]
"""

import feedparser 

# from process import process
from tweet import tweet

# from main.models import Episode, Raw_File, Cut_List

class pmc_tweet(tweet):

    ready_state = 5

    feed = ''

    def process_ep(self, ep):
        if self.options.verbose: print ep.id, ep.name
        show = ep.show
        client = show.client

        if not self.feed:
            self.feed = feedparser.parse('http://python.mirocommunity.org/feeds/category/pyohio-2011')

        urlss = [ (fe['link'], [ l['href'] for l in fe['links'] if l['rel']=='via' ][0]) for fe in self.feed['entries'] ]
        public_urls = [ u[0] for u in urlss if u[1].split('/')[-1] == ep.target]

        if public_urls:
            public_url = '/'.join(public_urls[0].split('/')[:-1])
            ep.public_url = public_url
            ep.save()
            prefix = "#%s #VIDEO" % show.client.slug
            tweet = self.mk_tweet(prefix, ep.name, ep.authors, public_url)
            user = 'nextdayvideo'

            ret=self.tweet_tweet(user, tweet)
        else:
            ret=False

        return ret


if __name__ == '__main__':
    p=pmc_tweet()
    p.main()

