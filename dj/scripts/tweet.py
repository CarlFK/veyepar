#!/usr/bin/python

# tweets #client.slug, #video, title and url
# shortens the URL and title if needed

# if over 140 char, url is shortened using bity,
# if still over, title is truncated.

import twitter

import urllib.request, urllib.error, urllib.parse
import pprint

import pw  # see pw_samp.py for sample.

from process import process

class tweet(process):

    ready_state = 10

    def shorten(self, url):
        return url # hack because auth broke:
        ## Out[15]: '{\n    "errorCode": 203, \n    "errorMessage": "You must be authenticated to access shorten", \n    "statusCode": "ERROR"\n}'

        d=dict(version='2.0.1',login=pw.bitly['user'], apikey=pw.bitly['password'], longurl=url)
        q = urllib.parse.urlencode(d)
        print(q)
        url = 'http://api.bit.ly/shorten?' + q
        data = eval(urllib.request.urlopen(url).read())
        print(data)
        return list(data['results'].values())[0]['shorturl']

    def mk_tweet(self,
            prefix, twitter_ids, video_name, authors, video_url, suffix):

        def j(*args):
            print('j:',args)
            # remove empty args
            args = [arg.strip() for arg in args[0] if arg]
            s = ' '.join(args)
            return s

        #lca2017 My Talk Title - @CarlFK http://youtu.be/123456
        if self.options.verbose:
            print(prefix, twitter_ids,
                    video_name, authors, video_url, suffix)

        if twitter_ids:
            message = j([
                prefix,
                twitter_ids,
                video_name,
                video_url,
                suffix])
        else:
            message = j([prefix, video_name, '-',
                authors, video_url, suffix ])

        if len(message) > 140:
            message = j([
                prefix, twitter_ids, video_name, video_url, suffix])
        if len(message) > 140:
            short_url = self.shorten(video_url)
            message = j([
                prefix, twitter_ids, video_name, short_url, suffix ])
        if len(message) > 140:
            video_name = video_name[:140 - len(message) - 3] + '...'
            message = j([
                prefix, twitter_ids, video_name, short_url, suffix])
        return message


    def tweet_tweet(self, user, tweet):
        if self.options.test:
            print('test mode:')
            print('user:', user)
            print(tweet)
            ret=False
        else:
            print('tweeting:', tweet)
            # print user,password
            t = pw.twit[user]
            api = twitter.Api(consumer_key=t['consumer_key'],
                     consumer_secret=t['consumer_secret'],
                     access_token_key=t['access_key'],
                     access_token_secret=t['access_secret'],
                     sleep_on_rate_limit=True)
            if self.options.verbose: print(api.VerifyCredentials())
            status = api.PostUpdate(tweet)
            d=status.AsDict()
            self.last_tweet = d
            self.last_tweet_url = "http://twitter.com/NextDayVideo/status/{}".format(d["id"], )
            # print("x-rate-limit-remaining: {}".format(d['x-rate-limit-remaining']))
            print(self.last_tweet_url)
            pprint.pprint(d)
            """
{'created_at': 'Wed Jan 23 04:54:06 +0000 2019',
 'hashtags': [{'text': 'lca2019'}],
 'id': 1087936488493457409,
 'id_str': '1087936488493457409',
 'lang': 'en',
 'source': '<a href="http://www.nextdayvideo.com" rel="nofollow">Veyepar '
           'AV</a>',
 'text': '#lca2019 Creating Ubuntu and Debian container base images, the old '
         'and  simple way - Hamish Coleman https://t.co/mkEZHhnffH',
 'urls': [{'expanded_url': 'http://youtu.be/OLFH4Ov6bJQ',
           'url': 'https://t.co/mkEZHhnffH'}],
 'user': {'created_at': 'Fri Nov 19 21:28:11 +0000 2010',
          'description': 'Conference/Event AV & video recording.  Record '
                         'today, watch online tomorrow.',
          'favourites_count': 1,
          'followers_count': 564,
          'friends_count': 2,
          'geo_enabled': True,
          'id': 217558518,
          'lang': 'en',
          'listed_count': 31,
          'location': 'Australia & United States',
          'name': 'Next Day Video',
          'profile_background_color': '000000',
          'profile_background_image_url': 'http://abs.twimg.com/images/themes/theme14/bg.gif',
          'profile_image_url': 'http://pbs.twimg.com/profile_images/1175824604/Screenshot-4_normal.png',
          'profile_link_color': 'FA743E',
          'profile_sidebar_fill_color': '000000',
          'profile_text_color': '000000',
          'screen_name': 'nextdayvideo',
          'statuses_count': 2910,
          'url': 'http://t.co/zibfPzbNyS'},
 'user_mentions': []}
"""

            ret=True

        return ret

    def retweet(self, user, status_id):
        print('retweenting:', status_id)
        t = pw.twit[user]
        api = twitter.Api(consumer_key=t['consumer_key'],
                 consumer_secret=t['consumer_secret'],
                 access_token_key=t['access_key'],
                 access_token_secret=t['access_secret'],
                 sleep_on_rate_limit=True)
        # if self.options.verbose: print(api.VerifyCredentials())

        status = api.PostRetweet(status_id)

        d=status.AsDict()
        pprint.pprint(d)

        return


    def ck_rate_limit(self):
        # https://python-twitter.readthedocs.io/en/latest/twitter.html?highlight=PostUpdate#
        InitializeRateLimit

    def process_ep(self, ep):
        show = ep.show
        client = show.client

        url = ep.public_url if ep.public_url \
                else ep.host_url

        if  show.client.tweet_prefix.startswith('@'):
            prefix = None
            suffix = show.client.tweet_prefix
        else:
            prefix = show.client.tweet_prefix
            suffix = ''

        # remove commas
        if ep.twitter_id is None \
                or not ep.twitter_id:
            twitter_ids = ""
        else:
            twitter_ids = []
            for tid in ep.twitter_id.split(','):
                tid = tid.strip()
                if not tid.startswith('@'):
                    tid = "@" + tid
                twitter_ids.append(tid)
            twitter_ids = ' '.join(twitter_ids)


        tweet = self.mk_tweet(
                prefix,
                twitter_ids, ep.name, ep.authors, url,
                suffix)

        # keys to twitter account creds
        users = client.tweet_id.split(',')
        users = [u.strip() for u in users]

        # tweet primary tweet
        ret=self.tweet_tweet(users[0], tweet)

        if ret:
            ep.twitter_url = self.last_tweet_url
            ep.save()

            # retweet more:
            for user in users[1:]:
                d = self.last_tweet
                status_id = d['id']
                self.retweet(user, status_id)

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

    """
    user='test'
    status_id='1084321813675401216'
    p.retweet(user, status_id)
    """
    """
{'created_at': 'Mon Jan 14 02:27:18 +0000 2019',
 'hashtags': [],
 'id': 1084638052922716160,
 'id_str': '1084638052922716160',
 'lang': 'en',
 'retweet_count': 1,
 'retweeted': True,
 'retweeted_status': {'created_at': 'Mon Jan 14 02:27:17 +0000 2019',
                      'hashtags': [],
                      'id': 1084638051396014082,
                      'id_str': '1084638051396014082',
                      'lang': 'en',
                      'retweet_count': 1,
                      'retweeted': True,
                      'source': '<a '
                                'href="http://code.google.com/p/python-twitter/" '
                                'rel="nofollow">pt2</a>',
                      'text': "test @cfkarsten Let's make a Test (take 3!)",
                      'urls': [],
                      'user': {'created_at': 'Sun Oct 17 10:56:30 +0000 2010',
                               'default_profile': True,
                               'default_profile_image': True,
                               'followers_count': 1,
                               'id': 203869946,
                               'lang': 'en',
                               'name': 'test',
                               'profile_background_color': 'C0DEED',
                               'profile_background_image_url': 'http://abs.twimg.com/images/themes/theme1/bg.png',
                               'profile_image_url': 'http://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png',
                               'profile_link_color': '1DA1F2',
                               'profile_sidebar_fill_color': 'DDEEF6',
                               'profile_text_color': '333333',
                               'screen_name': 'veyepar_test',
                               'statuses_count': 197},
                      'user_mentions': [{'id': 50915517,
                                         'name': 'Carl F. Karsten',
                                         'screen_name': 'cfkarsten'}]},
 'source': '<a href="http://code.google.com/p/python-twitter/" '
           'rel="nofollow">pt2</a>',
 'text': "RT @veyepar_test: test @cfkarsten Let's make a Test (take 3!)",
 'urls': [],
 'user': {'created_at': 'Sun Oct 17 10:56:30 +0000 2010',
          'default_profile': True,
          'default_profile_image': True,
          'followers_count': 1,
          'id': 203869946,
          'lang': 'en',
          'name': 'test',
          'profile_background_color': 'C0DEED',
          'profile_background_image_url': 'http://abs.twimg.com/images/themes/theme1/bg.png',
          'profile_image_url': 'http://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png',
          'profile_link_color': '1DA1F2',
          'profile_sidebar_fill_color': 'DDEEF6',
          'profile_text_color': '333333',
          'screen_name': 'veyepar_test',
          'statuses_count': 197},
 'user_mentions': [{'id': 203869946,
                    'name': 'test',
                    'screen_name': 'veyepar_test'},
                   {'id': 50915517,
                    'name': 'Carl F. Karsten',
                    'screen_name': 'cfkarsten'}]}
"""


