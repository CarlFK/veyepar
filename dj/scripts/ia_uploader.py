#!/usr/bin/env python
# -*- coding: utf-8 -*-

# archive_uploader.py 
# archive.org specific code

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
    # ProgressFile is a subclass of the Python open class
    # as data is read, it prints a visible progress bar 
    from progressfile import ProgressFile
except ImportError:
    # If ProgressFile is not available, default to Python's open
    ProgressFile = open

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


class Uploader(object):

    # input attributes:
    user = '' # key to lookup user/pw in pw.py
    pathname = ''  # path to video file to upload`
    slug = "" # slug used to make URL

    verbose = False
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
            'title':self.meta['title'],
            'creator':self.meta['authors'],
            # this is visible on the web page under 'Keywords: '
            'subject':self.meta['tags'],
            # this is visible on the web page as the license
            # 'licenseurl', 'http://creativecommons.org/licenses/by/4.0/',
            'licenseurl': "http://creativecommons.org/licenses/by/3.0/",
            # this is visible on the web page as the description
            'description':self.meta['description'],
            'publicdate':self.meta['start'],
        }


        if self.test:
            # meta['x-archive-meta-collection'] = 'test_collection'
            meta['collection'] = 'test_collection'

        return meta


    def upload(self):

        print "Uploading file to Archive.org..."

        auth = archive[self.user] ## from dict of credentials 
        md = self.get_metadata()
        pf = ProgressFile(self.pathname, 'r')
        item = ia.get_item(self.slug)

        try:

            # actually upload
            ret = item.upload(pf, metadata=md, 
                    access_key=auth['access'], secret_key=auth['secret'],
                    ignore_preexisting_bucket=True,
                    verbose=self.verbose)

            if self.debug_mode:
                import code; code.interact(local=locals())
                
            self.new_url = item.url
                
            print( "ia: {}".format(self.new_url))
            ret = True

        except HTTPError as e: 

            print( "ia_uploader.py", e )

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
    u.slug = unicode(u.slug)
    u.meta = {
      'title': u"test title",
      'description': u"test description",
      'language': "eng",
      'tags': [u'test', u'tests', ],
      'authors':u'people',
      'start':datetime.datetime.now()
    }
    """
    u.meta = {
     'authors': [u'Simon Cross'],
     'category': 22,
     'description': u'Adrianna Pi\u0144ska',
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
        print u.new_url
    else:
        print u.ret_text


if __name__ == '__main__':

    options, args = parse_args(sys.argv)
    test_upload(options)

