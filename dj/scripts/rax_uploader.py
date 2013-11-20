# rax_uploader.py 
# rackspace cdn (openhatch) specific code

# caled from post_rak.py 
# that is a lie.  it is really called from post_yt.py.  


import pyrax
pyrax.set_setting("identity_type", "rackspace")

from pyrax.exceptions import PyraxException
import urllib 

# The following 2 imports are wrapped in try/except so that 
# this code will run without any additional files.
try:
    # ProgressFile is a subclass of the python open class
    # as data is read, it prints a visible progress bar 
    from youtube_uploader import ProgressFile
except ImportError:
    # or just use python's open for testing
    ProgressFile = open

try:
    # read credentials from a file
    from pw import rax 
except ImportError:
    # https://mycloud.rackspace.com/account#settings
    # Username:
    # API Key:

    # you can fill in your credentials here
    # but better to put in pw.py 
    rax={
            "testact":{
                'user': "abc",
                "api_key": "123"
                }   
            }   

def auth(upload_user="test"):

    auth = rax[upload_user] ## from dict of credentials 
    pyrax.set_credentials( username=auth['user'], password=auth['api_key'])
    return pyrax.cloudfiles


class Uploader(object):

    # input attributes:
    pathname = ''  # path to video file to upload

    user = '' # key to lookup user/pw in rax{} typically stored in pw.py
    bucket_id = "" # archive/s3 butcket, or container ID for rax

    debug_mode = False

    # return attributes:
    ret_text = ''  # TODO: return error text
    new_url = ''

    def upload(self):

        cf = auth(self.user)
        container = cf.get_container(self.bucket_id)

        pf = ProgressFile(self.pathname, 'r')

        try:

            # actually upload
            obj = container.upload_file(pf)

            if self.debug_mode:
                import code
                code.interact(local=locals())
            
            # urllib.quote  
            # filenames may have chars that need to be quoted for a URL.
            # cdn_streaming because.. video? (not sure really)
            self.new_url = container.cdn_streaming_uri +"/"+ urllib.quote(obj.name)
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

    # senseable values for testing.
    u.user = 'testact'
    u.bucket_id = 'testing' # define this on rackspace gui
    u.pathname = '/home/carl/Videos/veyepar/test_client/test_show/mp4/Lets_make_a_Test.mp4'
    u.debug_mode = False ## True drops to a >>> prompt after upload

    ret = u.upload()

    print u.new_url

