# x2.prg
# aka the gist.

# PYVIDEO_URL = 'http://localhost:8081/api/v1/'
# USERNAME = 'carl'
# API_KEY = 'a50ad70ab3d8334c4c60dddb0992d774c0db4a98'

PYVIDEO_URL = 'http://pyvideo.org:9000/api/v1/'
USERNAME = 'willkg'
API_KEY = 'b8a9ffda15c76a438599683ce9346fcacfb27786'

VIDEO = {
    # 1 if LIVE and 2 if DRAFT.
    u'state': 1,

    # Here you can add whiteboard notes regarding curator/editor
    # issues.
    u'whiteboard': u'',

    # The title of the video. No HTML.
    u'title': u'',

    # The category (conference title) of the video. e.g. "PyCon 2012".
    # The category needs to exist in the db before you can use it.
    u'category': u'',

    # The summary for the video. Should be a paragraph tops. Use
    # HTML: <p>, <ul>, <ol>, <li>, ...
    u'summary': u'',

    # Description for the video. Can be as long as you like. Use
    # HTML: <p>, <ul>, <ol>, <li>, ...
    u'description': u'',

    # Audio/Video quality notes. e.g. "Audio is mono only." "Silence
    # until minute 3--but then audio works after that."
    u'quality_notes': u'',

    # This is the slug. Should be like the title, but lowercase
    # letters, numbers and hyphens only.
    #
    # Two videos can't have the same slug, so if you bump into
    # something like that, add a 2 at the end.
    #
    # e.g. 'big-data-de-duping'
    u'slug': u'',

    # The url for where the video is posted on the internet.
    u'source_url': u'',

    # Text describing the copyright/license if any.
    u'copyright_text': u'',

    # List of zero or more tags associated with this video.
    # These will get created if they don't already exist in the
    # db.
    # e.g. ['web', 'slumber', 'tastypie']
    u'tags': [],

    # List of zero or more speakers associated with this video.
    # These will get created if they don't already exist in the
    # db.
    # e.g. ['Carl Karsten', 'Chris Webber']
    u'speakers': [],

    # Datetime that it was added to pyvideo.org. This should be
    # now. Format is YYYY-MM-DDThh:mm:ss'
    u'added': u'2012-06-15T20:34:32',

    # Date the video was recorded. Note that this is just a date--no
    # time.
    u'recorded': u'2012-06-14',

    # Lanugage of the video. Should probably be 'English'
    u'language': u'English',

    # Url for the thumbnail.
    u'thumbnail_url': u'',

    # Url and filesize in bytes of the ogv media file if any.
    u'video_ogv_url': u'',
    u'video_ogv_length': None,

    # Url and filesize in bytes of the mp4 media file if any.
    u'video_mp4_url': u'',
    u'video_mp4_length': None,

    # Url and filesize in bytes  of the webm media file if any.
    u'video_webm_url': u'',
    u'video_webm_length': None,

    # Url and filesize in bytes  of the flv media file if any.
    u'video_flv_url': u'',
    u'video_flv_length': None,

    # Embed code if there's a flash version.
    u'embed': u''
}

CATEGORY = {
    # The category kind. This was a dumb idea I had to group
    # categories. Anyhow, the kind of conferences is 1.
    u'kind': 1,

    # General name of the conference.
    # e.g. "PyCon US"
    u'name': u'',

    # Name of this specific instance of the conference.
    # e.g. "PyCon US 2012"
    u'title': u'',

    # Description of the conference.
    u'description': u'',

    # URL for the conference site.
    u'url': u'',

    # Whiteboard notes for curating/editing
    u'whiteboard': u'',

    # The date this conference started (used solely for sorting
    # conferences by date).
    u'start_date': None,

    # Slug for the conference. Lowercase letters, numbers and hyphens.
    # e.g. "pycon-us-2012"
    u'slug': u'bostonpy',
}

# This is just a lib that makes doing REST stuff easier.
import slumber

# Create an api object with the target api root url.
api = slumber.API(PYVIDEO_URL)

# Grab a video just to see what it looks like.
# It's a dict with two keys: meta and objects. meta has some info in
# it for paging, counts, and stuff. objects has a list of the objects
# you asked for. In this case, it's videos.
video = api.video.get(limit=1)

cat_data = {
    'kind': 1,
    'name': 'CarlCon',
    'title': 'CarlCon 2012',
    'description': 'Where awesome people get to be Carl for a day.',
    'url': 'http://carlcon.us/',
    'whiteboard': '',
    'start_date': '2012-07-11',
    'slug': 'carlcon-2012'
}

# hunt down any previous data that looks like the data we are working with
# and kill it.
cats = api.category.get()
for cat in cats['objects']:
    if cat['slug'] == cat_data['slug']:
        cat_id = cat['id']
        api.category(cat_id).delete(username=USERNAME, api_key=API_KEY)

# Let's create a category.
try:
    cat = api.category.post(cat_data, username=USERNAME, api_key=API_KEY)
    pass
except Exception as exc:
    # TODO: OMG gross.
    error_lines = [line for line in exc.content.splitlines()
                   if 'exception_value' in line]
    if error_lines:
        for line in error_lines:
            print line
    raise


# print "Created category: ", cat

# Let's populate a video object and push it.
video_data = {
    'state': 1,
    'whiteboard': '',
    'title': 'Carl with Pants',
    'category': 'CarlCon 2012',
    'summary': '<p>Carl shows off his magic pants again.</p>',
    'description': '<p>In a death-defying display of crazed agility, Carl shows off his magic pants and how he can take them off and put them on using only a straw.</p>\n<p>This video covers</p><ul><li>pants</li><li>straws</li></ul>',
    'quality_notes': '',
    'slug': 'carl-with-pants',
    'source_url': 'http://youtube.com/whatever',
    'copyright_text': '',
    'tags': ["pants"],
    'speakers': ["Carl Karsten"],
    'added': '2012-06-15T20:34:32',
    'recorded': '2012-06-14',
    'language': 'English',
    'thumbnail_url': 'http://example.com/thumbnail.jpg',

    # I have no media for this video--just a lousy embed code. So I
    # leave all these "blank".
    'video_ogv_url': u'',
    'video_ogv_length': None,
    'video_mp4_url': u'',
    'video_mp4_length': None,
    'video_webm_url': u'',
    'video_webm_length': None,
    'video_flv_url': u'',
    'video_flv_length': None,

    'embed': '<object>whatever</object>'
}

# api.video(vid['id']).delete(username=USERNAME, api_key=API_KEY)
try:
    # Let's create this video with an HTTP POST.
    # Oh wait--I hate everything I did! DELETE IT ALL!
    vid = api.video.post(video_data, username=USERNAME, api_key=API_KEY)
except Exception as exc:
    # TODO: OMG gross.
    error_lines = [line for line in exc.content.splitlines()
                   if 'exception_value' in line]
    if error_lines:
        for line in error_lines:
            print line
    raise

print "Created video: ", vid

# Oh Noes! We made a mistake and forgot to add Ryan.
vid['speakers'].append('Ryan "Flying Monkey" Verner')

try:
    vid = api.video(vid['id']).put(video_data, username=USERNAME, api_key=API_KEY)
except Exception as exc:
    # TODO: OMG gross.
    error_lines = [line for line in exc.content.splitlines()
                   if 'exception_value' in line]
    if error_lines:
        for line in error_lines:
            print line
    raise
