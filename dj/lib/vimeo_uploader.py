#!/usr/bin/python
# -*- coding: utf-8 -*-

# /vimeo_uploader.py
# uploads to viemo

"""
README
FIXME

To run this standalone:

1.
pip install git+https://github.com/CarlFK/google-api-python-client.git#egg=googleapiclient
pip install google-api-python-client

2. Get a client ID (defines who is running this code)
https://developers.google.com/identity/protocols/OAuth2ServiceAccount#creatinganaccount
Warning: Keep your client secret private. If someone obtains your client secret, they could use it to consume your quota, incur charges against your Google APIs Console project, and request access to user data.

3. To define what youtube account will be uploaded to,
   the first time you run this it will prompt for a key:
    Go to the following link in your browser:
    https://accounts.google.com/o/oauth2/auth?...
    Enter verification code:
A token gets saved in oauth.json and will be used for all subsiquent runs.

4. if you don't give it a --pathname, it tries to upload itself,
which errors with:
    ResumableUploadError ... "reason": "badContent", "message": "Media type 'text/x-python' is not supported.

"""

import argparse
from collections import namedtuple

import http.client
import httplib2
import os
import random
import sys
import time

import pprint

from urllib.parse import urlparse
from urllib.parse import parse_qs

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow

# The following import is wrapped in try/except so that
# this code will run without any additional files.
try:
    # read credentials from a file
    from pw import yt
except ImportError:
    # you can fill in your credentials here for dev
    # but better to put in pw.py
    yt={
            "test":{ 'filename': "oauth.json" }
            }


def clean_description(description):

    """
"The property value has a maximum length of 5000 bytes and may contain all valid UTF-8 characters except < and >."
https://developers.google.com/youtube/v3/docs/videos#properties
    """

    # replace <- and -> with arrows, < > with pointy things.
    # another way of coding the arrows: u"\N{LEFTWARDS ARROW}"
    description = description.replace("<-","←")
    description = description.replace("->","→")
    description = description.replace("<","‹")
    description = description.replace(">","›")
    return description

# FIXME  Replace all the youtube stuff wiht viemo stuff
class Uploader():

    # input attributes:
    user = 'test'
    pathname = ''
    meta = {}
    old_url = ''
    debug=False

    # return attributes:
    ret_text = ''
    new_url = ''

    def set_permission(self, video_url, privacyStatus='public'):

        youtube = get_authenticated_service(user_key=self.user)
        video_id = get_id_from_url(video_url)

        videos_update_response = youtube.videos().update(
            part='status',
            body={
                'id':video_id,
                'status': {
                    'privacyStatus': privacyStatus,
                    'embeddable': True,
                    'license': 'creativeCommon',
                    'publicStatsViewable': True,
                },
            },
        ).execute()

        """
        >>> videos_update_response
        {u'status': {u'publicStatsViewable': False, u'privacyStatus':
        u'public', u'uploadStatus': u'processed', u'license': u'youtube',
        u'embeddable': False}, u'kind': u'youtube#video', u'etag':
        u'"fpJ9onbY0Rl_LqYLG6rOCJ9h9N8/yzjxcIfiMnHpq7I5wbMY44afabU"', u'id':
        u'cUvNths_5RA'}
        """

        stat = videos_update_response['status']['privacyStatus']
        if stat != privacyStatus:
            pprint.pprint(videos_update_response)
            import code; code.interact(local=locals())


        return True

    def add_to_playlist(self, video_url, playlist_id):
        youtube = get_authenticated_service(user_key=self.user)
        video_id = get_id_from_url(video_url)
        youtube.playlistItems().insert(
            part='snippet',
            body={
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id,
                    },
                },
            }
        ).execute()
        return True

    def delete_video(self, video_url):
        # https://developers.google.com/youtube/v3/docs/videos/delete
        # https://google-api-client-libraries.appspot.com/documentation/youtube/v3/python/latest/youtube_v3.videos.html

        youtube = get_authenticated_service(user_key=self.user)
        video_id = get_id_from_url(video_url)

        videos_delete_response = youtube.videos().delete(
                id=video_id
                    ).execute()

        print(("deleted {}".format(video_url)))

        # videos_delete_response is ''
        return videos_delete_response


    def upload(self):

        youtube = get_authenticated_service(user_key=self.user)

        if self.debug:
            print(self.pathname)
            pprint.pprint(self.meta)

        self.meta['description'] = clean_description(
                self.meta['description'])

        status, response = initialize_upload(youtube,
                self.pathname, self.meta)

        self.response = response

        self.new_url = "http://youtu.be/{id}".format(**response)
        self.thumbnail = "https://i.ytimg.com/vi/{id}/hqdefault.jpg".format(**response)

        return True

def make_parser():

    parser = argparse.ArgumentParser(description="""
    Find a video file and upload it to youtube.
    """)

    parser.add_argument('--user', '-u', default='test',
            help="key into pw['yt'][key]: secrets. default: test")

    # find the test file
    ext = "mp4"
    veyepar_dir = os.path.expanduser('~/Videos/veyepar')
    test_dir = os.path.join(veyepar_dir,"test_client/test_show/",ext)
    test_file = os.path.join(test_dir,"Lets_make_a_Test.%s" % (ext))
    if not os.path.exists(test_file):
        # if we can't find a video to upload, upload this .py file!
        test_file = os.path.abspath(__file__)

    parser.add_argument('--pathname', '-f', default=test_file,
                        help='file to upload.')

    parser.add_argument('--delete',
                        help='existing youtube vid to delete.')

    parser.add_argument('--debug_mode', '-d', default=False,
            action='store_true',
            help='whether to drop to prompt after upload. default: False')

    return parser


def test_upload(args):

    u = Uploader()

    u.meta = {
      'title': "test title",
      'description': "<test description",
      'category': 22, # 22 is maybe "Education",
      'tags': ['test', 'tests', ],
      'privacyStatus':'private',
      # 'latlon': (37.0,-122.0),
      'license':'creativeCommon',
    }

    u.user = args.user
    u.debug_mode = args.debug_mode
    u.pathname = args.pathname

    ret = u.upload()
    if ret:
        print(u.new_url)
        print(u.thumbnail)
        return u.new_url
    else:
        print(u.ret_text)

def test_set_pub(args,video_url):

    u = Uploader()
    u.user=args.user
    u.set_permission(video_url)

    return


def test_set_unlisted(args,video_url):

    u = Uploader()
    u.user=args.user
    u.set_permission(video_url, privacyStatus='unlisted')

    return


def test_delete(args, video_url):

    u = Uploader()
    u.user=args.user
    u.delete_video(video_url)

    return

"""
errors!
A retriable HTTP error 500 occurred:
{
 "error": {
  "errors": [
   {
    "domain": "global",
    "reason": "backendError",
    "message": "Backend Error"
   }
  ],
  "code": 500,
  "message": "Backend Error"
 }
}

Sleeping 0.040870 seconds and then retrying...

raise HttpError(resp, content, uri=self.uri)
apiclient.errors.HttpError: <HttpError 410 when requesting https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&alt=json&part=snippet%2Cstatus returned "Backend Error">
"""

def main():

    parser = make_parser()
    args = parser.parse_args()

    if args.delete:
        # url = "http://youtu.be/C3U5G5uxgz4"
        url = args.delete
        test_delete(args,url)

    url = test_upload(args)

    # test_set_pub(args,url)
    # test_set_unlisted(args, "http://youtu.be/zN-drQny-m4")
    # test_set_unlisted(args, url)

if __name__ == '__main__':
    main()

