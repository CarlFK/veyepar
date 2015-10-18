#!/usr/bin/env python
# -*- coding: utf-8 -*-

# foo_uploader.py 
# template for future upload 

import sys
import optparse

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


def auth(upload_user):
    # 
    """ get a service connection to archive.org
    """
    auth = archive[upload_user] ## from dict of credentials 
    connection = boto.connect_s3( auth['access'], auth['secret'], 
            host='s3.us.archive.org', is_secure=False, 
            calling_format=boto.s3.connection.OrdinaryCallingFormat())

    return connection


class Uploader(object):

    # input attributes:
    user = '' # key to lookup user/pw in pw.py
    pathname = ''  # path to video file to upload`
    key_id = "" # slug used to make URL

    debug_mode = False
    test = False

    # return attributes:
    ret_text = ''
    new_url = ''

    def upload(self):

        print "Uploading file to foo..."

        service = auth(self.user)

        pf = ProgressFile(self.pathname, 'r')

        try:

            # actually upload
            ret = key.set_contents_from_file(pf)

            if self.debug_mode:
                import code; code.interact(local=locals())

            self.new_url = 
            print( "foo: {}".format(self.new_url))
            ret = True

        except Exception as e:

            print e

            # self.ret_text = "internet archive error: %s" % ( e.body )

            import code; code.interact(local=locals())

            ret = False

        return ret


def parser.parse_args(argv):

    parser = optparse.OptionParser()

    parser.add_option("-v", "--verbose", action="store_true",
           default=False, 
           help="Be more verbose during uploads")

    parser.add_option('--user', '-u', 
            default='test',
            help='archive user. default: test')

    parser.add_option('--filename', '-f', 
            default=os.path.abspath(__file__),
            help='archive user. default: this .py file')

    parser.add_option('--bucket', '-b', default='test_ndv_archive_uploader',
            help='bucket. default: test_ndv_archive_uploader'
            '    test_ndv_archive_uploader is owned by test account.'
            '    test_ndv_auth_keys is owned by ndv account')

    parser.add_option('--debug_mode', '-d', 
            default=False, action='store_true',
            help='whether to drop to prompt after upload. default: False')

    parser.add_option('--test', '-t', 
            action='store_true',
            default=True, 
            help='whether to delete after 30 days. default: True')

    options, args = parser.parse_args(args)
    return options, args


### Smoke test
def test_upload(args):
    u = Uploader()
    u.user = args.user
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

    options, args = parse_args(sys.argv)
    test_upload(args)

