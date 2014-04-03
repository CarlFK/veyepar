#!/usr/bin/python
# youtube_v3_uploader.py
# uploads to youtube using google's api v3

import httplib
import httplib2
import os
import random
import sys
import time

import pprint

from urlparse import urlparse
from urlparse import parse_qs

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow


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
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
  httplib.IncompleteRead, httplib.ImproperConnectionState,
  httplib.CannotSendRequest, httplib.CannotSendHeader,
  httplib.ResponseNotReady, httplib.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

def get_authenticated_service(args):

  flow = flow_from_clientsecrets( CLIENT_SECRETS_FILE, 
          scope=YOUTUBE_READ_WRITE_SCOPE,)

  # how and where tokens are stored
  storage = Storage("oauth2.json")
  # http://google-api-python-client.googlecode.com/hg/docs/epy/oauth2client.multistore_file-module.html 

  credentials = storage.get()

  if credentials is None or credentials.invalid:
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
    part=",".join(body.keys()),
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
        chunksize=5 * 1024 * 1024, resumable=True)
  )

  status, response = resumable_upload(insert_request)

  return status, response

# This method implements an exponential backoff strategy to resume a
# failed upload.
def resumable_upload(insert_request):
  response = None
  error = None
  retry = 0
  while response is None:
    try:
      print "Uploading file..."
      status, response = insert_request.next_chunk()
      if 'id' in response:
        print "Video id '%s' was successfully uploaded." % response['id']
      else:
        exit("The upload failed with an unexpected response: %s" % response)
    except HttpError, e:
      if e.resp.status in RETRIABLE_STATUS_CODES:
        error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                             e.content)
      else:
        raise
    except RETRIABLE_EXCEPTIONS, e:
      error = "A retriable error occurred: %s" % e

    if error is not None:
      print error
      retry += 1
      if retry > MAX_RETRIES:
        exit("No longer attempting to retry.")

      max_sleep = 2 ** retry
      sleep_seconds = random.random() * max_sleep
      print "Sleeping %f seconds and then retrying..." % sleep_seconds
      time.sleep(sleep_seconds)

  return status, response

def update_video(youtube, options):

  videos_update_response = youtube.videos().update(
    part='status',
    body={
        'id':options['video_id'],
        'status':options['privacyStatus'],
        }
    ).execute()


def get_id_from_url(url):
    print url
    o = urlparse(url)
    print o
    if o.query:
        # http://www.youtube.com/watch?v=akAtm7SnzWg
        q = parse_qs(o.query)
        print q
        id = q['v'][0]
    else:
        # http://youtu.be/akAtm7SnzWg
        id = o.path[1:]

    return id

class Uploader():

    # input attributes:
    files = []
    meta = {}
    old_url = ''
    debug=False

    # return attributes:
    ret_text = ''
    new_url = ''

    def set_permission(self, video_url, privacyStatus='public'):

        video_id = get_id_from_url(video_url)

        args = {'video_id':video_id,
            'privacyStatus':privacyStatus,
            }

        youtube = get_authenticated_service({'noauth_local_webserver':True})
        update_video(youtube, args)

    def upload(self):

        youtube = get_authenticated_service({'noauth_local_webserver':True})

        pathname = self.files[0]['pathname']
        meta = self.meta

        if self.debug:
            print pathname
            pprint.pprint(meta)

        if self.debug:
            pass
            # import pdb; pdb.set_trace()

        status, response = initialize_upload(youtube, pathname, meta)

        self.response = response

        self.new_url = "http://youtu.be/%s" % ( response['id'] )

        return 


def test_upload():
 
    meta = {
      'description': ("test " * 5) + "1", 
      'title': "test title",
      'category': 22, # 22 is maybe "Education",
      'tags': [u'test', u'tests', ],
      'privacyStatus':'private',
      # 'latlon': (37.0,-122.0),
    }

    # find the test file
    ext = "webm"
    veyepar_dir = os.path.expanduser('~/Videos/veyepar')
    test_dir = os.path.join(veyepar_dir,"test_client/test_show/",ext)
    test_file = os.path.join(test_dir,"Lets_make_a_Test.%s" % (ext))

    u = Uploader()
    # youtube only takes one file,
    # but the veyepar api takes a list
    # so make a list of one file.
    u.files = [{'pathname':test_file, 'ext':ext}]
    u.meta = meta
    # u.user = 'test'

    u.debug=True

    ret = u.upload()

    print ret
    print u.new_url


def test_set_pub():
    video_url = "https://www.youtube.com/watch?v=MN1y5lvSHQ8"

    u = Uploader()
    # u.user="test"
    # u.debug=True
    u.set_permission(video_url)

if __name__ == '__main__':
    # test_set_pub()
    test_upload()

