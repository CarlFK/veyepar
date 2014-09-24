#!/usr/bin/python
# -*- coding: utf-8 -*-

# youtube_v3_uploader.py
# uploads to youtube using google's api v3

# https://developers.google.com/youtube/v3/
# https://developers.google.com/youtube/v3/code_samples/python
# https://github.com/youtube/api-samples/tree/master/python

# https://github.com/google/oauth2client

# https://developers.google.com/api-client-library/python/guide/aaa_oauth

import argparse
from collections import namedtuple
import progressfile

"""
to use progressfile you need to patch 
@ 418  ~/.virtualenvs/veyepar/local/lib/python2.7/site-packages/apiclient/http.py

    if isinstance(filename,file):
        fd = filename
        filename = fd.name
    else:
        fd = open(self._filename, 'rb')

"""
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
from apiclient.errors import HttpError, ResumableUploadError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow

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
        httplib2.HttpLib2Error, IOError, httplib.NotConnected,
        httplib.IncompleteRead, httplib.ImproperConnectionState,
        httplib.CannotSendRequest, httplib.CannotSendHeader,
        httplib.ResponseNotReady, httplib.BadStatusLine)

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
  print "Uploading file..."
  while response is None:
    try:

      status, response = insert_request.next_chunk()
      if response is None:
          print status.progress()

      if 'id' in response:
         print "Video id '%s' was successfully uploaded." % response['id']
      else:
        exit("The upload failed with an unexpected response: %s" % response)

    except ResumableUploadError, e:
      print e.content
      import code; code.interact(local=locals())
      raise e

    except HttpError, e:
      if e.resp.status in RETRIABLE_STATUS_CODES:
        error = "A retriable HTTP error %d occurred:\n%s" % (
                e.resp.status, e.content )
      else:
        raise

    except RETRIABLE_EXCEPTIONS, e:
      error = "A retriable error occurred: %s" % e

    except Exception, e:
      import code; code.interact(local=locals())


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

def get_id_from_url(url):
    o = urlparse(url)
    if o.query:
        # http://www.youtube.com/watch?v=akAtm7SnzWg
        q = parse_qs(o.query)
        print q
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
    description = description.replace("<-",u"←")
    description = description.replace("->",u"→")
    description = description.replace("<",u"‹")
    description = description.replace(">",u"›")
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
                'status':privacyStatus,
                }
            ).execute()


        return True

    def upload(self):

        youtube = get_authenticated_service(user_key=self.user)

        if self.debug:
            print self.pathname
            pprint.pprint(self.meta)

        pf = progressfile.ProgressFile(self.pathname)

        self.meta['description'] = clean_description(
                self.meta['description'])

        status, response = initialize_upload(youtube, pf, self.meta)

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
        test_file = os.path.abspath(__file__),

    parser.add_argument('--pathname', '-f', default=test_file,
                        help='file to upload.')

    parser.add_argument('--debug_mode', '-d', default=False, 
            action='store_true', 
            help='whether to drop to prompt after upload. default: False')

    return parser


def test_upload(args):

    u = Uploader()
   
    description = ("test " * (5/5)) + "Look as this -> >1< <- I rule."

    u.meta = {
      'description': description,
      'title': "test title",
      'category': 22, # 22 is maybe "Education",
      'tags': [u'test', u'tests', ],
      'privacyStatus':'private',
      # 'latlon': (37.0,-122.0),
    }

    u.user = args.user
    u.debug_mode = args.debug_mode
    u.pathname = args.pathname

    ret = u.upload()
    if ret:
        print u.new_url
        return u.new_url
    else:
        print u.ret_text

def test_set_pub(video_url):
    
    u = Uploader()
    u.set_permission(video_url)

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

    test_set_pub(url)

