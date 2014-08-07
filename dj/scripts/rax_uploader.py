# rax_uploader.py 
# rackspace cdn (openhatch) specific code

# caled from post_rak.py 
# that is a lie.  it is currently called from post_yt.py.  

import argparse

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

    user = 'testact' # key to lookup user/pw in rax{} typically stored in pw.py
    bucket_id = "example" # archive/s3 butcket, or container ID for rax
    key_id = "" # orbject name (the key in a key value store)

    debug_mode = False

    # return attributes:
    ret_text = ''  # TODO: return error text
    new_url = ''

    def upload(self):

        cf = auth(self.user)

        if self.debug_mode:
            print "cf.get_all_containers", cf.get_all_containers()
        container = cf.get_container(self.bucket_id)

        # check if object already exists:
        # if same name and same md5, don't bother re-uploading.
        try:
            obj = container.get_object(self.key_id)
            already_there = obj.etag == pyrax.utils.get_checksum(
                    self.pathname,)
            ret = True
        except pyrax.exceptions.NoSuchObject as e:
            already_there = False

        if not already_there:

            done=False
            while not done:

                pf = ProgressFile(self.pathname, 'r')

                try:

                    # actually upload
                    obj = container.upload_file(pf, obj_name = self.key_id)
                    print "no exception"
                    

                    if self.debug_mode:
                        import code
                        code.interact(local=locals())
                    
                    done = True
                    ret = True

                except pyrax.exceptions.ClientException as e:
                    print e
                    print e.code, e.details, e.message

                    if e.code==408:
                        print "looping..."
                        continue

                    print e
                    # self.ret_text = "rax error: %s" % ( e.body )

                    import code
                    code.interact(local=locals())


                except Exception as e:

                    print e
                    # self.ret_text = "rax error: %s" % ( e.body )

                    import code
                    code.interact(local=locals())

                    ret = False

        # urllib.quote  
        # filenames may have chars that need to be quoted for a URL.
        # cdn_streaming because.. video? (not sure really)
        # self.new_url = container.cdn_streaming_uri +"/"+ urllib.quote(obj.name)
        self.new_url = container.cdn_uri +"/"+ urllib.quote(obj.name)

        return ret

def pars_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--pathname', default=
  '/home/carl/Videos/veyepar/test_client/test_show/webm/Lets_make_a_Test.webm',
            help='pathname of file to upload.')

    parser.add_argument('--user', default="testact",
            help="key to lookup credintials from pw.py")

    parser.add_argument('--container', default="example",
            help="container to upload to.")

    parser.add_argument('--obj_name', default=
            "/test_client/test_show/webm/Lets_make_a_Test.webm",
            help="container to upload to.")

    parser.add_argument('--debug', 
            help="Drops to a >>> prompt after upload")

    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = pars_args()

    u = Uploader()

    # senseable values for testing.
    u.pathname = args.pathname
    u.user = args.user
    u.bucket_id = args.container # define this on rackspace gui
    u.key_id = args.obj_name
    u.debug_mode = args.debug

    ret = u.upload()

    print u.new_url

