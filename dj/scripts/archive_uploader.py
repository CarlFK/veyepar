# youtube_uploader.py 
# archive.org specific code

# caled from post_arc.py 

# which someday will be jsut post.py with a arc parameter.

import pw
import progressbar

# following http://docs.pythonboto.org/en/latest/s3_tut.html
# http://archive.org/catalog.php?history=1&identifier=nextdayvideo.test
# http://archive.org/details/nextdayvideo.test/foobar 

import boto

widgets = [
        'Upload: ',
        progressbar.Percentage(), ' ',
        progressbar.Bar(marker=progressbar.RotatingMarker()), ' ', 
        progressbar.ETA(), ' ',
        progressbar.FileTransferSpeed(),
        ]

def progress(current, blocksize, total):
    """
    Displaies upload percent done, bytes sent, total bytes.
    """
    elapsed = datetime.datetime.now() - self.start_time 
    remaining_bytes = total-current
    if elapsed.seconds: 
        bps = current/elapsed.seconds
        remaining_seconds = remaining_bytes / bps 
        eta = datetime.datetime.now() + datetime.timedelta(seconds=remaining_seconds)
        sys.stdout.write('\r%3i%%  %s of %s MB, %s KB/s, elap/remain: %s/%s, eta: %s' 
          % (100*current/total, current/(1024**2), total/(1024**2), bps/1024, stot(elapsed.seconds), stot(remaining_seconds), eta.strftime('%H:%M:%S')))
    else:
        sys.stdout.write('\r%3i%%  %s of %s bytes: remaining: %s'
          % (100*current/total, current, total, remaining_bytes, ))


class ProgressFile(file):
    def __init__(self, *args, **kw):
        file.__init__(self, *args, **kw)

        self.seek(0, 2)
        self.len = self.tell()
        self.seek(0)

        self.pbar = progressbar.ProgressBar(
            widgets=widgets, maxval=self.len)
        self.pbar.start()

    def size(self):
        return self.len

    def __len__(self):
        return self.size()

    def read(self, size=-1):
        if (size > 1e3):
                size = int(1e3)
        try:
            self.pbar.update(self.tell())
            return file.read(self, size)
        finally:
            self.pbar.update(self.tell())
            if self.tell() >= self.len:
                self.pbar.finish()

class Uploader(object):

    # input attributes:
    files = []
    thumb = ''
    meta = {}
    upload_user = ''
    old_url = ''
    # user=''
    private=False
    bucket_id = ""
    key_id = ""

    # return attributes:
    ret_text = ''
    new_url = ''

    def auth(self):

        auth = pw.archive[self.upload_user]
        connection = boto.connect_s3( auth['access'], auth['secret'], 
                host='s3.us.archive.org', is_secure=False)

        return connection

    def upload(self):

        service = self.auth()
        bucket = service.get_bucket(self.bucket_id)
        key = boto.s3.key.Key(bucket)
        key.key = self.key_id

        pathname= self.files[0]['pathname']
        # pf = ProgressFile(pathname, 'r')
        
        try:
            # actually upload
            key.set_contents_from_filename(pathname)

            self.new_url = key.generate_url(0)
            ret = True

        except:
            import code
            code.interact(local=locals())
            ret = False

        return ret

if __name__ == '__main__':
    u = Uploader()
    u.meta = {
     'title': "test title",
     'description': "test description",
     'tags': ['tag1', 'tag2'],
     'category': "Education",
     'hidden': 0,
     'latlon': (37.0,-122.0)
    }

    u.files = [{'pathname':'/home/carl/Videos/veyepar/test_client/test_show/mp4/Test_Episode.mp4'}]
    u.upload_user = 'cfkarsten'
    u.bucket_id = 'test.buck'
    u.key_id='test'

    ret = u.upload()

    print u.new_url




