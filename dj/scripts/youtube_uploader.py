# youtube_uploader.py 
# youtbe specific code

# caled from post_yt.py 
# which someday will be jsut post.py with a yt parameter.

# http://code.google.com/apis/youtube/1.0/developers_guide_python.html
# http://code.google.com/apis/youtube/2.0/reference.html

import gdata.media
import gdata.geo
import gdata.youtube
import gdata.youtube.service

from gdata.media import YOUTUBE_NAMESPACE
from atom import ExtensionElement

from gdata.youtube.service import YouTubeError

import pw
import progressbar


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
    user=''
    private=False
    debug_mode=False

    # return attributes:
    ret_text = ''
    new_url = ''

    def auth(self):
         
        yt_service = gdata.youtube.service.YouTubeService()
        gauth = pw.yt[self.user]

        yt_service.email = gauth['email']
        yt_service.password = gauth['password']
        yt_service.source = 'video eyebaal review'
        yt_service.developer_key = gauth['dev_key']
        yt_service.client_id = self.user

        yt_service.ProgrammaticLogin()

        return yt_service
       
    def media_group(self):
        # prepare a media group object to hold our video's meta-data
        media_group = gdata.media.Group(
            title=gdata.media.Title(
                text=self.meta['title']),
            description=gdata.media.Description(
                description_type='plain',
                text=self.meta['description']),
            keywords=gdata.media.Keywords(
                text=','.join(self.meta['tags'] )),
            category=[gdata.media.Category(
                # label=self.meta['category'],
                # text=self.meta['category'],
                label="Education",
                text="Education",
                scheme='http://gdata.youtube.com/schemas/2007/categories.cat',
                )],
            player=None
            )

        if self.private:
            media_group.private=gdata.media.Private()

        return media_group


    def geo(self):
        # prepare a geo.where object to hold the geographical location
        # of where the video was recorded
        where = gdata.geo.Where()
        # where.set_location((37.0,-122.0))
        where.set_location(self.meta['latlon'])

        return where

 
    def upload(self):

        yt_service = self.auth()

        video_entry = gdata.youtube.YouTubeVideoEntry(
                media=self.media_group())

        if self.meta.has_key('latlon'):
            video_entry.geo = self.geo()

        # add some more metadata -  more tags
        print self.meta['tags']
        video_entry.AddDeveloperTags(self.meta['tags'])

        pathname= self.files[0]['pathname']

        pf = ProgressFile(pathname, 'r')
        try:
            # actually upload
            self.new_entry = yt_service.InsertVideoEntry(video_entry, pf)
            self.ret_text = self.new_entry.__str__()
            link = self.new_entry.GetHtmlLink()
            self.new_url = link.href.split('&')[0]
            print self.new_url
            ret = True

        except gdata.youtube.service.YouTubeError as e:
            self.ret_text = 'request: %s\nerror: %s' % (video_entry.ToString(), e.__str__())
            ret = False
            if self.debug_mode:
                import code
                code.interact(local=locals())

        return ret
    
    def extra_stuff(self):

        upload_status = yt_service.CheckUploadStatus(new_entry)

        if upload_status is not None:
            video_upload_state = upload_status[0]
            detailed_message = upload_status[1]

            print video_upload_state
            print detailed_message

        entry = yt_service.GetYouTubeVideoEntry(video_id=video_id)
        print 'Video flash player URL: %s' % entry.GetSwfUrl()

        # show alternate formats
        for alternate_format in entry.media.content:
            if 'isDefault' not in alternate_format.extension_attributes:
              print 'Alternate format: %s | url: %s ' % (alternate_format.type,
                                                         alternate_format.url)

        # show thumbnails
        for thumbnail in entry.media.thumbnail:
            print 'Thumbnail url: %s' % thumbnail.url

if __name__ == '__main__':
    u = Uploader()

    u.meta = {
      'title': "test title",
      'description': "test description",
      #'description': "test " * 100,
      #'tags': ['tag1', 'tag2'],
      'tags': [u'enthought', u'scipy_2012', u'Bioinformatics Mini-Symposia', u'DanielWilliams'],
      'category': "Education",
      'latlon': (37.0,-122.0)
    }
    """
    u.meta = {
      'title': "Python @ Life",
      'description': "test " * 100,
      'tags': [u'enthought', u'scipy_2012', u'Bioinformatics Mini-Symposia', u'DanielWilliams'],
      'category': "Education",
      'latlon': (37.0,-122.0)
    }
    """
    print u.meta

    u.files = [{'pathname':'/home/juser/Videos/veyepar/test_client/test_show/mp4/Test_Episode.mp4', 'ext':'mp4'}]
    u.user = 'veyepar_test'
    # u.private = True

    ret = u.upload()
    if ret: print u.new_entry.id.text
    print u.ret_text

    # import code
    # code.interact(local=locals())
    # import pdb
    # pdb.set_trace()


"""
https://code.google.com/p/gdata-python-client/issues/detail?id=350
Support YouTube access controls 

http://stackoverflow.com/questions/6770362/upload-a-video-to-youtube-using-the-python-api-and-set-it-as-unlisted

##############################33
from gdata.media import YOUTUBE_NAMESPACE
from atom import ExtensionElement

# set video as unlisted
kwargs = {
    "namespace": YOUTUBE_NAMESPACE,
    "attributes": {'action': 'list', 'permission': 'denied'},
}
extension = ([ExtensionElement('accessControl', **kwargs)])

# create the gdata.youtube.YouTubeVideoEntry
video_entry = gdata.youtube.YouTubeVideoEntry(media=my_media_group,
    geo=where, extension_elements=extension)

"""
