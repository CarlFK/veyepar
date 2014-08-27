#!/usr/bin/env python
# -*- coding: utf-8 -*-

# archive_uploader.py 
# archive.org specific code

import argparse
import os

import boto
import boto.s3.connection

"""
Uploader for Internet Archive that uses boto and the s3 archive interface

Boto Docs:
  * http://docs.pythonboto.org/en/latest/s3_tut.html
  * http://boto.readthedocs.org/en/latest/ref/file.html#boto.file.connection.FileConnection.get_bucket

Archive s3 Docs:
  * http://archive.org/help/abouts3.txt

Test buckets that have been created for checking this script:
  * https://archive.org/details/test_ndv_auth_keys (owned by ndv user)
  * https://archive.org/details/test_ndv_archive_uploader (owned by test user)

"""


try:
    # ProgressFile is a subclass of the python open class
    # as data is read, it prints a visible progress bar 
    from progressfile import ProgressFile
except ImportError:
    # If ProgressFile is not available, default to open
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


def auth(upload_user):
    """ get a service connection to archive.org
    """
    auth = archive[upload_user] ## from dict of credentials 
    connection = boto.connect_s3( auth['access'], auth['secret'], 
            host='s3.us.archive.org', is_secure=False, 
            calling_format=boto.s3.connection.OrdinaryCallingFormat())

    return connection


def make_bucket(conn, bucket_id, meta={}):
    """ make a new bucket

    conn: service connection to archive.org
    bucket_id: bucket name
    meta: dictionary of archive.org meta data

    """

    headers = {
        # mediatype and collection are values that are specific to archive.org
        # do not change these unless you know what you are doing
        'x-archive-meta-mediatype': meta.get('mediatype', 'movies'),
        'x-archive-meta-collection': meta.get('collection', 'opensource_movies'),
        # you can change these
        # this is visible on the web page under 'Keywords: '
        'x-archive-meta-subject': meta.get('subject', 'testing'),
        # this is visible on the web page as the license
        'x-archive-meta-licenseurl': meta.get('licenseurl', 'http://creativecommons.org/licenses/by/4.0/'),
        # this is visible on the web page as the description
        'x-archive-meta-description': meta.get('description', 'testing uploader script'),
        # this is not visible, it's in the _meta.xml. maybe it should be date?
        'x-archive-meta-year': meta.get('year', '2014'),
    }
    return conn.create_bucket(bucket_id, headers=headers)


class Uploader(object):

    # input attributes:
    pathname = ''  # path to video file to upload`

    user = '' # key to lookup user/pw in pw.py
    bucket_id = "" # archive/s3 butcket - There is some limit on size?
    key_id = "" # slug used to make URL

    debug_mode = False
    test = False

    # return attributes:
    ret_text = ''
    new_url = ''

    def upload(self):

        service = auth(self.user)

        headers={}
        if self.test:
            headers['x-archive-meta-collection'] = 'test_collection'
        bucket = service.get_bucket(self.bucket_id, headers=headers)
        key = boto.s3.key.Key(bucket)
        key.key = self.key_id

        pf = ProgressFile(self.pathname, 'r')

        try:

            # actually upload
            ret = key.set_contents_from_file(pf)
            # ret is the number of bytes in the file

            if self.debug_mode:
                import code
                code.interact(local=locals())

            self.new_url = key.generate_url(0)
            ret = True

        except Exception as e:

            """
              $ curl s3.us.archive.org -v -H x-archive-simulate-error:SlowDown
              To see a list of errors s3 can simulate, you can do:
              $ curl s3.us.archive.org -v -H x-archive-simulate-error:help
            """
            print e
            self.ret_text = "internet archive error: %s" % ( e.body )

            import code
            code.interact(local=locals())

            ret = False

        return ret


### Smoke test

def make_parser():
    parser = argparse.ArgumentParser(description="""
    Upload this file to archive.org
    """)
    parser.add_argument('--user', '-u', default='test',
                        help='archive user. default: test')

    parser.add_argument('--filename', '-f', 
            default=os.path.abspath(__file__),
                        help='archive user. default: this .py file')

    parser.add_argument('--bucket', '-b', default='test_ndv_archive_uploader',
                        help='bucket. default: test_ndv_archive_uploader'
                        '    test_ndv_archive_uploader is owned by test account.'
                        '    test_ndv_auth_keys is owned by ndv account')
    parser.add_argument('--debug_mode', '-d', default=False, action='store_true',
                        help='whether to drop to prompt after upload. default: False')
    parser.add_argument('--test', '-t', default=True, action='store_true',
                        help='whether to delete after 30 days. default: True')
    return parser


def test_upload(args):
    u = Uploader()
    u.user = args.user
    u.bucket_id = args.bucket
    u.debug_mode = args.debug_mode
    u.test = args.test
    u.pathname = args.filename
    u.key_id = os.path.basename(u.pathname)

    ret = u.upload()
    if ret:
        print u.new_url
    else:
        print u.ret_text


if __name__ == '__main__':

    parser = make_parser()
    args = parser.parse_args()

    test_upload(args)
