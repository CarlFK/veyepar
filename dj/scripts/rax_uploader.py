# rax_uploader.py 
# rackspace cdn (openhatch) specific code

# caled from post_rak.py 
# that is a lie.  it is really called from post_yt.py.  


import pprint

import pyrax
from pyrax.exceptions import PyraxException
from urllib import quote

from collections import defaultdict

# The following 2 imports are wrapped in try/except so that 
# this code will run without any additional files.
try:
    # ProgressFile is a subclass of the python open class
    # as data is read, it prints a visible progress bar 
    from youtube_uploader import ProgressFile
except ImportError:
    ProgressFile = open

try:
    # read credentials from a file
    from pw import rax 
except ImportError:
    # you can fill in your credentials here
    # but better to put in pw.py so that they don't leak
    rax={
            "test":{
                'user': "abc",
                "api_key": "123"
                }   
            }   

def auth(upload_user="test"):

    auth = rax[upload_user] ## from dict of credentials 
    
    pyrax.set_setting("identity_type", "rackspace")
    pyrax.set_credentials( username=auth['user'], password=auth['api_key'])
    return pyrax.cloudfiles


class Uploader(object):

    # input attributes:
    pathname = ''  # path to video file to upload`

    user = '' # key to lookup user/pw in pw.py
    bucket_id = "testing" # archive/s3 butcket - There is some limit on size?
    key_id = "" # slug used to make URL

    debug_mode = False
    test = False

    # return attributes:
    ret_text = ''
    new_url = ''

    def upload(self):

        cf = auth(self.user)
        container = cf.get_container(self.bucket_id)

        results = defaultdict(dict)

        pf = ProgressFile(self.pathname, 'r')

        try:

            # actually upload
            obj = container.upload_file(pf)

            if self.debug_mode:
                import code
                code.interact(local=locals())

            self.new_url = container.cdn_streaming_uri +"/"+ quote(obj.name)
            ret = True

        except Exception as e:

            print e
            # self.ret_text = "rax error: %s" % ( e.body )

            import code
            code.interact(local=locals())

            ret = False

        return ret


if __name__ == '__main__':

    u = Uploader()

    u.user = 'test'
    u.bucket_id = 'testing' # we defined this on rackspace gui
    u.key_id='test.mp4'
    u.pathname = '/home/carl/Videos/veyepar/test_client/test_show/mp4/Lets_make_a_Test.mp4'
    u.debug_mode = False ## True drops to a >>> prompt after upload
    u.test = True ## will be deleted in 30 days

    ret = u.upload()

    print u.new_url

