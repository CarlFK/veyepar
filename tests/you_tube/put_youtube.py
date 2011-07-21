
import gdata.media
import gdata.geo
import gdata.youtube
import gdata.youtube.service

import pw


# prepare a media group object to hold our video's meta-data
my_media_group = gdata.media.Group(
  title=gdata.media.Title(text='My Test Movie'),
  description=gdata.media.Description(description_type='plain',
                                      text='My description'),
  keywords=gdata.media.Keywords(text='cars, funny'),
  category=[gdata.media.Category(
      text='Autos',
      scheme='http://gdata.youtube.com/schemas/2007/categories.cat',
      label='Autos')],
  player=None
)


# prepare a geo.where object to hold the geographical location
# of where the video was recorded
where = gdata.geo.Where()
where.set_location((37.0,-122.0))

# create the gdata.youtube.YouTubeVideoEntry to be uploaded
video_entry = gdata.youtube.YouTubeVideoEntry(media=my_media_group,
                                              geo=where)

developer_tags = ['some_tag_01', 'another_tag']
video_entry.AddDeveloperTags(developer_tags)

# set the path for the video file binary
video_file_location = '/home/carl/temp/Test_Episode.mp4'

yt_service = gdata.youtube.service.YouTubeService()
yt_service.email = pw.gdata['email']
yt_service.password = pw.gdata['password']
yt_service.source = 'video eyebaal review'
yt_service.developer_key = pw.gdata['dev_key']
yt_service.client_id = 'veyepar_test'
yt_service.ProgrammaticLogin()

new_entry = yt_service.InsertVideoEntry(video_entry, video_file_location)

video_id = new_entry.id.text
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

import code
code.interact(local=locals())

# import pdb
# pdb.set_trace()

