#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ia_uploader.py
# internet archive.org specific code

import optparse
import os
import sys
import datetime

import internetarchive as ia

from requests.exceptions import HTTPError

"""
Uploader for Internet Archive that uses internetarchive
https://pypi.python.org/pypi/internetarchive/0.9.6
https://github.com/jjjake/internetarchive

Archive s3 Docs:
  * http://archive.org/help/abouts3.txt

Test buckets that have been created for checking this script:
  * https://archive.org/details/test_ndv_auth_keys (owned by ndv user)
  * https://archive.org/details/test_ndv_archive_uploader (owned by test user)

"""

try:
    # read credentials from a file
    from pw import archive
except ImportError:
    # you can fill in your credentials here
    # but better to put in pw.py so that they don't leak
    archive={
            "test":{
                'access': "abc",
                "secret": "123"
                }
            }

def translitr(s):
    for f,t in [
        ('\xf6',"o"),
        ('\u2019',"'"),
        ('\u2013',"-"),
        ('\u2014','-'),
        ('\u2019',"'"),
        ('\u201c','"'),
        ('\u2022',"o"),
        ('\u2039',"<"),
            ]:
        s = s.replace(f,t)

    return s

class Uploader(object):

    # input attributes:
    user = '' # key to lookup user/pw in pw.py
    pathname = ''  # path to video file to upload`
    slug = "" # slug used to make URL

    progress = True # ia :param verbose: Display upload progress.
    verbose = False # spew extra stuff
    debug_mode = False
    test = False

    meta = {
              'title':'',
              'description':'',
              'language': "eng",
              'tags':[],
              }

    # return attributes:
    ret_text = ''
    new_url = ''

    def get_metadata(self):

        meta = {
            'mediatype': "movies",
            'language': self.meta['language'],
            'collection': 'opensource_movies',
            'title':translitr(self.meta['title']),
            'creator':self.meta['authors'],
            # this is visible on the web page under 'Keywords: '
            'subject':self.meta['tags'],
            # this is visible on the web page as the license
            'licenseurl': self.meta.get('licenseurl',
                'http://creativecommons.org/licenses/by/4.0/'),
            # this is visible on the web page as the description
            'description':translitr(self.meta['description']),
            'publicdate':self.meta['start'].isoformat(),
        }

        if self.test:
            meta['collection'] = 'test_collection'

        return meta


    def upload(self):

        print("Uploading file to Archive.org...")

        auth = archive[self.user] ## from dict of credentials
        md = self.get_metadata()

        item = ia.get_item(self.slug)

        try:

            # actually upload
            ret = item.upload(self.pathname, metadata=md,
                    access_key=auth['access'], secret_key=auth['secret'],
                    # ignore_preexisting_bucket=True,
                    verbose=self.progress)

            if self.debug_mode:
                import code; code.interact(local=locals())

            # https://archive.org/details/lca2016-Internet_Archive_Universal_Access_Open_APIs
            self.new_url = "https://archive.org/details/{}".format(self.slug)
            print(( "ia: {}".format(self.new_url)))
            ret = True

        except HTTPError as e:

            print(( "ia_uploader.py", e ))

            # self.ret_text = "internet archive error: %s" % ( e.body )

            import code; code.interact(local=locals())

            ret = False

        return ret


def parse_args(argv):

    parser = optparse.OptionParser()

    parser.add_option('--user', '-u',
            default='test',
            help='archive user. default: test')

    parser.add_option('--filename', '-f',
            default=os.path.abspath(__file__),
            help='archive user. default: this .py file')

    parser.add_option('--debug', '-d',
            default=False, action='store_true',
            help='whether to drop to prompt after upload. default: False')

    parser.add_option("-v", "--verbose", action="store_true",
           default=False,
           help="Be more verbose during uploads")

    parser.add_option('--test', '-t',
            action='store_true',
            default=True,
            help='whether to delete after 30 days. default: True')

    options, args = parser.parse_args(argv)
    return options, args


### Smoke test
def test_upload(args):

    u = Uploader()
    u.user = args.user
    u.debug_mode = args.debug
    # u.test = args.test
    u.test = True
    u.verbose = args.verbose
    u.pathname = args.filename
    # u.pathname = u'/home/carl/Videos/veyepar/pyconza/pyconza2015/mp4/PyCon_Montréal_in_30_min.mp4'
    u.slug = os.path.splitext(os.path.basename(u.pathname))[0]
    # u.slug = u"PyCon_Montréal"
    # u.slug = "PyCon_Mont"
    u.slug = str(u.slug)
    u.meta = {
      'title': "test title",
      'description': "test description",
      'language': "eng",
      'tags': ['test', 'tests', ],
      'authors':'people',
      'start':datetime.datetime.now()
    }
    """
    u.meta = {
     'authors': [u'Simon Cross'],
     'category': 22,
     'description': u'Adrianna Pi\\u0144ska',
     'language': 'eng',
     'privacyStatus': 'unlisted',
     'start': datetime.datetime(2015, 10, 2, 15, 30),
     'tags': [u'pyconza', u'pyconza2015', u'python', u'SimonCross'],
     'title': u'Friday Lightning Talks'}
    """

    import logging
    logging.basicConfig(level=logging.DEBUG)
    ret = u.upload()
    if ret:
        print(u.new_url)
    else:
        print(u.ret_text)


if __name__ == '__main__':

    options, args = parse_args(sys.argv)
    test_upload(options)

