# youtube_uploader.py 
# youtbe specific code

# caled from post_yt.py 
# which someday will be jsut post.py with a yt parameter.

import gdata.media
import gdata.geo
import gdata.youtube
import gdata.youtube.service

import pw

class Uploader(object):

    # input attributes:
    files = []
    thumb = ''
    meta = {}
    upload_user = ''
    old_url = ''
    user=''

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
                label=self.meta['category'],
                text=self.meta['category'],
                scheme='http://gdata.youtube.com/schemas/2007/categories.cat',
                )],
            player=None
            )

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
                media=self.media_group(), geo=self.geo())

        # add some more metadata -  more tags!
        video_entry.AddDeveloperTags(self.meta['tags'])

        # actually upload
        self.new_entry = yt_service.InsertVideoEntry(video_entry, self.files[0])

        self.ret_text = self.new_entry.__str__()

        link = self.new_entry.GetHtmlLink()
        self.new_url = link.href 

        return True
    
    def extra_stuff():

        print video_id
        video_id = video_id.split('/')[-1]
        print video_id

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
     'tags': ['tag1', 'tag2'],
     'category': "Education",
     'hidden': 0,
     'latlon': (37.0,-122.0)
    }

    u.files = ['/home/carl/Videos/veyepar/test_client/test_show/mp4/Test_Episode.mp4']
    u.user = 'cfkarsten'
    u.user = 'ndv'

    ret = u.upload()

    print "print u.new_entry.id.text"

    import code
    code.interact(local=locals())
    # import pdb
    # pdb.set_trace()



