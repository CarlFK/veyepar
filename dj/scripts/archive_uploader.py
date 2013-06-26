# archive_uploader.py 
# archive.org specific code

# caled from post_arc.py 
# that is a lie.  it is really called from post_yt.py.  


import sys
import pprint

import boto
import boto.s3.connection

# The following 2 imports are wrapped in try/except so that 
# this code will run without any additional files.
try:
    # print a visible progress bar as the file is read
    from youtube_uploader import ProgressFile
except ImportError:
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

# following http://docs.pythonboto.org/en/latest/s3_tut.html
# http://archive.org/catalog.php?history=1&identifier=nextdayvideo.test
# http://archive.org/details/nextdayvideo.test/foobar 

# for testing
# http://archive.org/~vmb/abouts3.html#testcollection
# x-archive-meta-collection:test_collection 

def auth(upload_user):

    auth = archive[upload_user] ## from dict of credentials 
    connection = boto.connect_s3( auth['access'], auth['secret'], 
            host='s3.us.archive.org', is_secure=False, 
            calling_format=boto.s3.connection.OrdinaryCallingFormat())

    return connection


def make_bucket(conn, bucket_id, meta):

    headers = {
            'x-archive-meta-mediatype':'movies',
            'x-archive-meta-collection':'opensource_movies',
            'x-archive-meta-year':meta['year'],
            'x-archive-meta-subject':meta['subject'],
            'x-archive-meta-licenseurl':meta['licenseurl'],
            'x-archive-meta-description':meta['description'],
    }

    return conn.create_bucket(bucket_id, headers=headers)


class Uploader(object):

    # input attributes:
    pathname = ''  # path to video file to upload`

    user = '' # key to lookup user/pw in pw.py
    bucket_id = "" # archive/s3 butcket - There is some limit on size?
    key_id = "" # slug used to make URL

    debug_mode = False

    # return attributes:
    ret_text = ''
    new_url = ''

    def upload(self):

        service = auth(self.user)
        bucket = service.get_bucket(self.bucket_id)
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

if __name__ == '__main__':

    u = Uploader()

    u.user = 'test'
    u.bucket_id = 'nextdayvideo.test'
    u.key_id='test.mp4'
    u.pathname = '/home/carl/Videos/veyepar/test_client/test_show/mp4/Lets_make_a_Test.mp4'
    u.debug_mode = False ## True drops to a >>> prompt after upload

    ret = u.upload()

    print u.new_url

