#!/usr/bin/env python
# -*- coding: utf-8 -*-

# swift_uploader.py 
# upload a file to an OpenStack host.

# TODO: 
# add support for returning the URL the file can be retrieved from. 

import os, sys
import argparse

import swiftclient

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

class Uploader(object):

    """
    Auth and Upload a file.
    """

    # input attributes:
    user = '' # key to lookup user/pw in pw.py
    pathname = ''  # path to video file to upload`
    bucket = "" # rackspace coiner/archive/s3 butcket, or container ID for rax
    key_id = "" # slug used to make URL

    verbose = False
    test = False
    debug_mode = False

    # return attributes:
    ret_text = ''
    new_url = ''

    def auth(self):
        """ 
        get a connection to the host
        """
        creds = swift[self.user] ## from dict of credentials 

        if self.verbose: print("authurl: {}".format(creds['authurl']))

        connection = swiftclient.Connection(**creds)

        return connection

    def upload(self):

        if self.verbose: print("Uploading file to CDN...")

        connection = self.auth()

        response_dict = {}

        with open(self.pathname, 'rb') as f:

            try:

                obj = connection.put_object(
                        self.bucket,
                        self.key_id,
                        contents = f,
                        response_dict = response_dict,
                        )

                if self.verbose: print("Uploaded.", response_dict)

                if self.debug_mode:
                    import code; code.interact(local=locals())

                # self.new_url = url
                # print(( "new_url: {}".format(self.new_url)))
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
            help='key to user auth. default: test')

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
    u.verbose = args.verbose
    u.debug_mode = args.debug_mode
    u.test = args.test
    u.pathname = args.filename
    u.bucket = args.bucket

    u.key_id = args.key if args.key else os.path.basename(u.pathname)

    ret = u.upload()


if __name__ == '__main__':

    # args = parse_args(sys.argv)
    args = parse_args()
    test_upload(args)

