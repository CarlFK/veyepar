#!/usr/bin/python
# -*- coding: utf-8 -*-

# youtube_v3_uploader.py
# uploads to youtube using google's api v3

"""
README

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

# https://developers.google.com/youtube/v3/
# https://developers.google.com/youtube/v3/code_samples/python
# https://github.com/youtube/api-samples/tree/master/python

# https://github.com/google/oauth2client

# https://developers.google.com/api-client-library/python/guide/aaa_oauth

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

"""
from apiclient.discovery import build
from apiclient.errors import HttpError, ResumableUploadError
from apiclient.http import MediaFileUpload
"""

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError, ResumableUploadError
from googleapiclient.http import MediaFileUpload

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


CLIENT_SECRETS_FILE = "client_secrets.json"

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
# YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account.
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (
        httplib2.HttpLib2Error, IOError, http.client.NotConnected,
        http.client.IncompleteRead, http.client.ImproperConnectionState,
        http.client.CannotSendRequest, http.client.CannotSendHeader,
        http.client.ResponseNotReady, http.client.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

def get_authenticated_service(user_key):

  args = namedtuple('flags', [ 
            'noauth_local_webserver',
            'logging_level'
            ] )

  args.noauth_local_webserver = True
  args.logging_level='ERROR'

  auth = yt[user_key] ## from dict of credentials 
  filename =auth['filename']

  # how and where tokens are stored
  storage = Storage(filename)

  # http://google-api-python-client.googlecode.com/hg/docs/epy/oauth2client.multistore_file-module.html 

  credentials = storage.get()

  if credentials is None or credentials.invalid:

      flow = flow_from_clientsecrets( CLIENT_SECRETS_FILE, 
              scope=YOUTUBE_READ_WRITE_SCOPE,)

      # do the "allow access" step, save token.
      credentials = run_flow(flow, storage, args)

  return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    http=credentials.authorize(httplib2.Http()))

def initialize_upload(youtube, filename, metadata):

  body={
          'snippet':{
              'title':metadata['title'],
              'description':metadata['description'],
              'tags':metadata['tags'],
              'categoryId':metadata['category'],
              },
          'status':{
              'privacyStatus':metadata['privacyStatus'],
              }
          }

  # Call the API's videos.insert method to create and upload the video.
  insert_request = youtube.videos().insert(
    part=",".join(list(body.keys())),
    body=body,
    # The chunksize parameter specifies the size of each chunk of data, in
    # bytes, that will be uploaded at a time. Set a higher value for
    # reliable connections as fewer chunks lead to faster uploads. Set a lower
    # value for better recovery on less reliable connections.
    #
    # Setting "chunksize" equal to -1 in the code below means that the entire
    # file will be uploaded in a single HTTP request. (If the upload fails,
    # it will still be retried where it left off.) This is usually a best
    # practice, but if you're using Python older than 2.6 or if you're
    # running on App Engine, you should set the chunksize to something like
    # 1024 * 1024 (1 megabyte).
    media_body=MediaFileUpload(filename, 
        # chunksize=5 * 1024 * 1024, resumable=True)
        # chunksize=5000 * 1024, resumable=True)
        chunksize=-1, resumable=True)
  )

  status, response = resumable_upload(insert_request)

  return status, response

# This method implements an exponential backoff strategy to resume a
# failed upload.
def resumable_upload(insert_request):
  response = None
  error = None
  retry = 0
  print("Uploading file to YouTube...")
  while response is None:

    try:
      status, response = insert_request.next_chunk()
      if response is None:
        print(status.progress())
        continue

      if 'id' in response:
         print("Video id '%s' was successfully uploaded." % response['id'])
      else:
        exit("The upload failed with an unexpected response: %s" % response)

    except ResumableUploadError as e:
      print(("ResumableUploadError e.content:{}".format(e.content)))
      print("to get out of this loop:\nimport sys;sys.exit()")
      import code; code.interact(local=locals())
      # raise e

    except HttpError as e:
      if e.resp.status in RETRIABLE_STATUS_CODES:
        error = "A retriable HTTP error %d occurred:\n%s" % (
                e.resp.status, e.content )
      else:
        print("to get out of this loop:\nimport sys;sys.exit()")
        import code; code.interact(local=locals())
        # raise e

    except RETRIABLE_EXCEPTIONS as e:
      error = "A retriable error occurred: %s" % e

    except Exception as e:
      print(("No clue what is going on.  e:{}".format(e)))
      print("to get out of this loop:\nimport sys;sys.exit()")
      import code; code.interact(local=locals())


    if error is not None:
      print(error)
      retry += 1
      if retry > MAX_RETRIES:
        exit("No longer attempting to retry.")

      max_sleep = 2 ** retry
      sleep_seconds = random.random() * max_sleep
      print("Sleeping %f seconds and then retrying..." % sleep_seconds)
      time.sleep(sleep_seconds)

  return status, response

def get_id_from_url(url):
    o = urlparse(url)
    if o.query:
        # http://www.youtube.com/watch?v=akAtm7SnzWg
        q = parse_qs(o.query)
        id = q['v'][0]
    else:
        # http://youtu.be/akAtm7SnzWg
        id = o.path[1:]

    return id

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
                'status':dict(privacyStatus=privacyStatus),
                }
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

        self.new_url = "http://youtu.be/%s" % ( response['id'] )

        return True

def make_parser():
    parser = argparse.ArgumentParser(description="""
    Find a video file and upload it to youtube.
    """)
    parser.add_argument('--user', '-u', default='test',
            help="key into pw['yt'][key]: secrets. default: test")
    # find the test file
    ext = "webm"
    veyepar_dir = os.path.expanduser('~/Videos/veyepar')
    test_dir = os.path.join(veyepar_dir,"test_client/test_show/",ext)
    test_file = os.path.join(test_dir,"Lets_make_a_Test.%s" % (ext))
    if not os.path.exists(test_file):
        # if we can't find a video to upload, upload this .py file!
        test_file = os.path.abspath(__file__)

    parser.add_argument('--pathname', '-f', default=test_file,
                        help='file to upload.')

    parser.add_argument('--debug_mode', '-d', default=False, 
            action='store_true', 
            help='whether to drop to prompt after upload. default: False')

    return parser


def test_upload(args):

    u = Uploader()
   
    u.meta = {
      'description': "test description",
      'title': "test title",
      'category': 22, # 22 is maybe "Education",
      'tags': ['test', 'tests', ],
      'privacyStatus':'private',
      # 'latlon': (37.0,-122.0),
    }

    u.user = args.user
    u.debug_mode = args.debug_mode
    u.pathname = args.pathname

    """
    import requests
    url = "http://5cda49ca88af98bf1f1e-b4c3b47b38bb1b572e0805ecabeeb59c.r76.cf2.rackcdn.com/10_05_52.ogv" 
    r=requests.get(url,stream=True)
    u.pathname = r.raw
    """

    ret = u.upload()
    if ret:
        print(u.new_url)
        return u.new_url
    else:
        print(u.ret_text)

def test_set_pub(args,video_url):
    
    u = Uploader()
    u.user=args.user
    u.set_permission(video_url)

    return


def test_delete(args,video_url):
    
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

if __name__ == '__main__':

    parser = make_parser()
    args = parser.parse_args()

    url = test_upload(args)
    # test_set_pub(args,url)
    test_delete(args,url)

