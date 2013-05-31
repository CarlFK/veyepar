# archive_uploader.py 
# archive.org specific code

# caled from post_arc.py 
# that is a lie.  it is really called from post_yt.py.  


import sys
import pprint

import boto
import boto.s3.connection

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



def auth(upload_user):

    auth = pw.archive[upload_user]
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

    # print conn, bucket_id
    # pprint.pprint(headers)
    return conn.create_bucket(bucket_id, headers=headers)

def hacky_test():

    meta = {
            'year':'2013',
            'subject':"PS:One;hackerspace",
            'licenseurl':'http://creativecommons.org/licenses/by/3.0/us/',
            'description':"<a href=http://pumpingstationone.org>Pumping Station One</a> is a hackerspace located in Chicago. Its mission is to foster a collaborative environment wherein people can explore and create intersections between technology, science, art, and culture."
    }

    conn =  auth("cfkarsten")
    print make_bucket(conn, "ndvps1", meta)

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

    # connection.create_bucket('codersquid.testvideos', headers={'x-archive-meta-collection':'opensource_movies'})

    u = Uploader()
    u.pathname = '/home/carl/cr.mpeg'
    u.pathname = '/home/carl/Videos/veyepar/test_client/test_show/mp4/Test_Episode.mp4'
    u.pathname = '/home/carl/mnt/mx04/Videos/veyepar/troy/nodepdx2013/mp4/ship_it.mp4'

    u.user = 'ndv'
    # u.user = 'cfkarsten'
    u.bucket_id = 'nextdayvideo.test'
    # u.bucket_id = 'nodepdx2013conference'
    # u.key_id='test'

    # u.key_id='shipit.mp4'
    u.key_id='test.mp4'
    u.debug_mode = False ## drops to a >>> prompt after upload

    ret = u.upload()

    print u.new_url

