#!/usr/bin/env python
# -*- coding: utf-8 -*-

# archive_uploader.py 
# archive.org specific code

import optparse
import os
import sys

import internetarchive as ia

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
            # this is visible on the web page under 'Keywords: '
            'subject':self.meta['title'],
            # this is visible on the web page as the license
            # 'licenseurl', 'http://creativecommons.org/licenses/by/4.0/',
            'licenseurl': "http://creativecommons.org/licenses/by/3.0/",
            # this is visible on the web page as the description
            'description':self.meta['description'],
            'tags':self.meta['tags'],
        }


        if self.test:
            meta['x-archive-meta-collection'] = 'test_collection'

        return meta


    def upload(self):

        print "Uploading file to Archive.org..."

        auth = archive[self.user] ## from dict of credentials 
        # auth['access'], auth['secret'] 

        md = self.get_metadata()

        pf = ProgressFile(self.pathname, 'r')

        item = ia.get_item(self.slug)

        try:

            # actually upload
            ret = item.upload(pf, metadata=md, 
                    access_key=auth['access'], secret_key=auth['secret'],
                    verbose=self.verbose)

            if self.debug_mode:
                import code; code.interact(local=locals())
                
            self.new_url = item.url
                
            print( "foo: {}".format(self.new_url))
            ret = True

        except Exception as e:

            print e

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
    u.test = args.test
    u.verbose = args.verbose
    u.pathname = args.filename
    u.slug = os.path.splitext(os.path.basename(u.pathname))[0]
    u.meta = {
      'title': "test title",
      'description': "test description",
      'language': "eng",
      'tags': [u'test', u'tests', ],
    }

    ret = u.upload()
    if ret:
        print u.new_url
    else:
        print u.ret_text


if __name__ == '__main__':

    options, args = parse_args(sys.argv)
    test_upload(options)

