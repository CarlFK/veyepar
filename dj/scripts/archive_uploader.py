# youtube_uploader.py 
# archive.org specific code

# caled from post_arc.py 

# which someday will be jsut post.py with a arc parameter.

import progressbar
from youtube_uploader import widgets
from youtube_uploader import progress
from youtube_uploader import ProgressFile


import pw
# pw.py looks like this:
"""
archive={
        "user":{
            'access': "abc",
            "secret": "123"
            }   
        }   
"""


# following http://docs.pythonboto.org/en/latest/s3_tut.html
# http://archive.org/catalog.php?history=1&identifier=nextdayvideo.test
# http://archive.org/details/nextdayvideo.test/foobar 

import boto
import boto.s3.connection

import sys

class Uploader(object):

    # input attributes:
    pathname = ''
    upload_user = ''
    bucket_id = ""
    key_id = ""
    debug_mode = False

    # return attributes:
    ret_text = ''
    new_url = ''

    def auth(self):

        auth = pw.archive[self.upload_user]
        connection = boto.connect_s3( auth['access'], auth['secret'], 
                host='s3.us.archive.org', is_secure=False, 
                calling_format=boto.s3.connection.OrdinaryCallingFormat())

        return connection

    def upload(self):

        service = self.auth()
        # bucket = service.create_bucket(self.bucket_id)
        bucket = service.get_bucket(self.bucket_id)
        key = boto.s3.key.Key(bucket)
        key.key = self.key_id

        pf = ProgressFile(self.pathname, 'r')

        try:
            # actually upload
            key.set_contents_from_file(pf)

            if self.debug_mode:
                import code
                code.interact(local=locals())

            self.new_url = key.generate_url(0)
            ret = True

        except:
            self.ret_text = "internet archive error: ", sys.exc_info()[0]
            ret = False

        return ret

if __name__ == '__main__':
    u = Uploader()
    u.pathname = '/home/carl/Videos/veyepar/test_client/test_show/mp4/Test_Episode.mp4'
    u.upload_user = 'cfkarsten'
    u.bucket_id = 'nextdayvideo.test'
    u.key_id='test'
    u.debug_mode = True

    ret = u.upload()

    print u.new_url

