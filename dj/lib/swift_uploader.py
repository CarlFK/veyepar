#!/usr/bin/env python
# -*- coding: utf-8 -*-

# foo_uploader.py 
# template for future upload 

import os, sys
import argparse
import pprint

import swiftclient

from swiftclient.service import SwiftError, SwiftService, SwiftUploadObject

try:
    # ProgressFile is a subclass of the Python open class
    # as data is read, it prints a visible progress bar 
    from progressfile import ProgressFile
except ImportError:
    # If ProgressFile is not available, default to Python's open
    ProgressFile = open

try:
    # read credentials from a file
    from pw import swift 
except ImportError:
    # you can fill in your credentials here
    # but better to put in pw.py so that they don't leak
    swift={
            "test":{
                'user': "abc",
                "key": "123",
                'authurl':'https://identity.api.rackspacecloud.com/v1.0/'
                }   
            }   


def auth(upload_user):
    # 
    """ get a service connection to archive.org
    """
    creds = swift[upload_user] ## from dict of credentials 
    connection = swiftclient.Connection(**creds)
    return connection

class Uploader(object):

    # input attributes:
    user = '' # key to lookup user/pw in pw.py
    pathname = ''  # path to video file to upload`
    bucket = "" # archive/s3 butcket, or container ID for rax
    key_id = "" # slug used to make URL

    debug_mode = False
    test = False

    # return attributes:
    ret_text = ''
    new_url = ''

    def upload(self):

        print("Uploading file to foo...")

        connection = auth(self.user)

        with open(self.pathname, 'rb') as f:

            try:

                # print('bucket', self.bucket)
                # print('key', self.key_id)

                obj = connection.put_object(
                        self.bucket,
                        self.key_id,
                        contents = f,
                        )

                if self.debug_mode:
                    import code; code.interact(local=locals())

                # self.new_url = url
                # print(( "foo: {}".format(self.new_url)))
                ret = True

            except Exception as e:

                print(e)

                # self.ret_text = "error: %s" % ( e.body )
                import code; code.interact(local=locals())

                ret = False

        return ret


def parse_args():

    parser = argparse.ArgumentParser(description="Upload a file to CDN")

    parser.add_argument("-v", "--verbose", action="store_true",
           default=False, 
           help="Be more verbose during uploads")

    parser.add_argument('--user', '-u', 
            default='test',
            help='archive user. default: test')

    parser.add_argument('--filename', '-f', 
            default=os.path.abspath(__file__),
            help='default: this .py file')

    parser.add_argument('--key', '-k', 
            help='object id')

    parser.add_argument('--bucket', '-b', default='example',
            help='bucket. default: example'
            '    aka continer name.'
            )

    parser.add_argument('--debug_mode', '-d', 
            default=False, action='store_true',
            help='whether to drop to prompt after upload. default: False')

    parser.add_argument('--test', '-t', 
            action='store_true',
            default=True, 
            help='whether to delete after 30 days. default: True')

    args = parser.parse_args()
    return args


### Smoke test
def test_upload(args):
    u = Uploader()
    u.user = args.user
    u.debug_mode = args.debug_mode
    u.test = args.test
    u.pathname = args.filename
    u.bucket = args.bucket

    u.key_id = args.key if args.key else os.path.basename(u.pathname)

    ret = u.upload()
    if ret:
        print(u.new_url)
    else:
        print(u.ret_text)


if __name__ == '__main__':

    # args = parse_args(sys.argv)
    args = parse_args()
    test_upload(args)

