#!/usr/bin/python
# -*- coding: utf-8 -*-

# youtube_v3_uploader.py
# uploads to youtube using google's api v3

"""
README

To run this standalone:

1. pip install google-api-python-client progressbar

2. Get a client ID (defines who is running this code)
https://salsa.debian.org/debconf-video-team/youtube#authentication
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

https://developers.google.com/youtube/v3/getting-started#quota
"""

# https://developers.google.com/youtube/v3/
# https://developers.google.com/youtube/v3/code_samples/python
# https://developers.google.com/identity/protocols/oauth2/scopes#youtube
# https://github.com/youtube/api-samples/tree/master/python

# https://developers.google.com/api-client-library/python/guide/aaa_oauth
# https://github.com/google/oauth2client

import argparse

import datetime
import http.client
import httplib2
import os
import random
import sys
import time

from collections import namedtuple
from pprint import pprint
from urllib.parse import urlparse
from urllib.parse import parse_qs

import progressbar as pb

from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError, ResumableUploadError
from googleapiclient.http import MediaIoBaseDownload

import googleapiclient.discovery
import googleapiclient.errors
import google.oauth2.credentials

from goauth import goog_start, goog_token, get_cred

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
# YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"


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

def resumable_upload(insert_request):
  # This method implements an exponential backoff strategy to resume a
  # failed upload.

  response = None
  error = None
  retry = 0

  widgets = ['Uploading: ', pb.Percentage(), ' ', pb.Bar(marker='0',left='[',right=']'), ' ', pb.ETA(), ' ', pb.FileTransferSpeed()] #see docs for other options
  pbar = pb.ProgressBar(widgets=widgets, maxval=1)
  pbar.start()

  print("Uploading file to YouTube...")
  while response is None:

    try:
      status, response = insert_request.next_chunk()
      if response is None:
          pbar.update(status.progress())
          continue

      if 'id' in response:
        print("Successful upload, Video id '%s'" % response['id'])
      else:
        exit( f"The upload failed with an unexpected response:\n{response=}")

    except ResumableUploadError as e:
      print(e)
      pprint(e.error_details)
      if e.error_details[0]['reason'] == 'quotaExceeded':
          sec = time_till_quota_reset(datetime.datetime.now(), 2)
          print(f'sleeping till time_till_quota_reset: {sec=}')
          time.sleep(sec)

      print("wake up!  quota refreshed?  Continuing to upload....")
      # print("to get out of this loop:\nimport sys;sys.exit()")
      # import code; code.interact(local=locals())

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

  pbar.finish()

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
    The property value has a maximum length of 5000 bytes and may contain all valid UTF-8 characters except < and >.
    https://developers.google.com/youtube/v3/docs/videos#properties
    """

    # replace <- and -> with arrows, < > with pointy things.
    # another way of coding the arrows: u"\N{LEFTWARDS ARROW}"
    description = description.replace("<-","←")
    description = description.replace("->","→")
    description = description.replace("<","‹")
    description = description.replace(">","›")

    return description

def time_till_quota_reset(current, reset_hour):
    # given now and what hour reset happens
    # returns seconds untill youtube quota reset

    reset = datetime.datetime(current.year, current.month, current.day, reset_hour) + datetime.timedelta(days=1)
    delta = reset - current
    seconds = delta.seconds # this drops delta.days, which covers the case of reset coming later in the same day. like 1am and reset it 2am.
    return seconds


class Uploader():

    # input attributes:
    client_secrets_file = 'client_secrets.json'
    token_file = 'oauth.json'
    pathname = ''
    meta = {}
    old_url = ''
    debug=False

    # return attributes:
    ret_text = ''
    new_url = ''

    def get_authenticated_service(self):

        credd = get_cred(self.token_file)
        credd = credd['credd'] # I don't like this.  Need to figure out who is storing what where.
        pprint(credd)
        credentials = google.oauth2.credentials.Credentials(**credd)

        api_service_name = "youtube"
        api_version = "v3"

        service = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return service


    def youtube_upload(self):

        service = self.get_authenticated_service()

        media_body=MediaFileUpload(
                self.pathname,
                chunksize=10* 1024 * 1024,
                resumable=True)

        insert_request = service.videos().insert(
            part=",".join(list(self.body.keys())),
            body=self.body,
            media_body=media_body,
        )

        status, response = resumable_upload(insert_request)

        return status, response


    def set_permission(self, video_url, privacyStatus='public'):
        # https://developers.google.com/youtube/v3/docs/videos/update
        # status.license

        # if you try to flip the status on a video uploaded to a different account...
        # >>> e.error_details
        # [{'message': 'Forbidden', 'domain': 'youtube.video', 'reason': 'forbidden'}]
        # >>> e.status_code
        # 403

        youtube = self.get_authenticated_service()
        video_id = get_id_from_url(video_url)

        videos_update_response = youtube.videos().update(
            part='status',
            body={
                'id':video_id,
                'status': {
                    'privacyStatus': privacyStatus,
                    'embeddable': True,
                    'publicStatsViewable': True,
                },
            },
        ).execute()

        """
        >>> videos_update_response
        {u'status': {u'publicStatsViewable': False, u'privacyStatus':
        u'public', u'uploadStatus': u'processed', u'embeddable': False},
        u'kind': u'youtube#video', u'etag':
        u'"fpJ9onbY0Rl_LqYLG6rOCJ9h9N8/yzjxcIfiMnHpq7I5wbMY44afabU"', u'id':
        u'cUvNths_5RA'}
        """

        stat = videos_update_response['status']['privacyStatus']
        if stat != privacyStatus:
            pprint(videos_update_response)
            import code; code.interact(local=locals())


        return True

    def set_description(self, video_url, description, title, categoryId):
        """You must specify a value for these properties:
    id
    snippet.title – This property is only required if the request updates the video resource's snippet.
    snippet.categoryId – This property is only required if the request updates the video resource's snippet.
        """

        youtube = self.get_authenticated_service()
        video_id = get_id_from_url(video_url)

        request = youtube.videos().update(
            part='snippet',
            body={
                'id': video_id,
                'snippet': {
                    'title': title,
                    'categoryId': categoryId,
                    'description': description,
                },
            },
        )

        response = request.execute()

        return True


    def add_to_playlist(self, video_url, playlist_id):
        youtube = self.get_authenticated_service()
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

    def playlist_item_delete(self, video_id, playlist_id):
        # https://developers.google.com/youtube/v3/docs/playlistItems/delete

        youtube = self.get_authenticated_service()
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

        youtube = self.get_authenticated_service()
        video_id = get_id_from_url(video_url)

        videos_delete_response = youtube.videos().delete(
                id=video_id
                    ).execute()

        print(("deleted {}".format(video_url)))

        # videos_delete_response is ''
        return videos_delete_response

    def comments(self, video_url, enable):
        """
        Not implemented, as YT Data v3 API doesn't support this :(
        https://issuetracker.google.com/issues/35174729
        https://issuetracker.google.com/issues/35175046
        """
        youtube = self.get_authenticated_service()
        video_id = get_id_from_url(video_url)
        # do_stuff_to_video_id
        # return response

    def get_captions(self, video_url, verbose=False):
        youtube = self.get_authenticated_service()
        video_id = get_id_from_url(video_url)

        video = youtube.captions().list(videoId=video_id, part='id').execute()

        if len(video['items']) != 1:
            print("FAILURE: Couldn't find exactly 1 caption.  Found: {}".format(video['items']))
            return None  # Can't get captions
        for captions in video['items']:
            caption_id = captions['id']

        return youtube.captions().download(id=caption_id, tfmt='srt').execute()


    def upload(self):

        if self.debug:
            print(self.pathname)
            pprint(self.meta)

        self.meta['description'] = clean_description(
                self.meta['description'])

        metadata = self.meta

        self.body={
          'snippet':{
              'title':metadata['title'],
              'description':metadata['description'],
              'categoryId':metadata['categoryId'],
              'tags':metadata['tags'],
              },
          'status':{
              'privacyStatus':metadata['privacyStatus'],
              'license':metadata.get('license', 'youtube'),
              }
          }


        status, response = self.youtube_upload()

        self.response = response

        self.new_url = "https://youtu.be/{id}".format(**response)
        self.thumbnail = "https://i.ytimg.com/vi/{id}/hqdefault.jpg".format(**response)

        return True


def test_upload(args):

    u = Uploader()

    u.meta = {
      'title': "test title",
      'description': "<test description",
      'categoryId': 22, # 22 is maybe "Education",
      'tags': ['test', 'tests', ],
      'privacyStatus':'unlisted', # 'private',
      # 'latlon': (37.0,-122.0),
      'license':'youtube',
    }

    u.token_file = args.token_file
    u.client_secrets_file=args.client_secrets_file
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
    u.token_file=args.token_file
    u.client_secrets_file=args.client_secrets_file
    u.set_permission(video_url)

    return


def test_set_description(args):

    desc = "This is Part II of a 2-part keynote for North Bay PyCon 2019 by Sha Wallace-Stepter and Jessica McKellar, and covers concrete actions technologists can take to change our criminal justice system. Find part I, on Sha's life story in the prison system, here: https://youtu.be/jNBsrLzHVgM"

    desc = """
Jonathan Bisson

#ps1 #FPGA #OpenSource #LiteX

Introduce the basics of FPGA programming using Verilog on an Open Source and Free toolchain.
"""

    u = Uploader()
    u.token_file=args.token_file
    # u.client_secrets_file=args.client_secrets_file
    u.set_description(args.up_desc, description=desc)

    return

def test_set_unlisted(args,video_url):

    # VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

    u = Uploader()
    u.token_file=args.token_file
    u.client_secrets_file=args.client_secrets_file
    u.set_permission(video_url, privacyStatus='unlisted')

    return


def test_set_no_comments(args,video_url):
    # WIP?
    # no worky :(

    u = Uploader()
    u.client_secrets_file=args.client_secrets_file
    u.token_file=args.token_file
    u.set_permission(video_url, privacyStatus='unlisted')

    return


def test_delete(args, video_url):

    u = Uploader()
    u.client_secrets_file=args.client_secrets_file
    u.token_file=args.token_file
    u.delete_video(video_url)

    return


def test_caption(token_file, vid_id):

    youtube = get_authenticated_service(token_file=token_file)
    request = youtube.captions().download(
            id=vid_id,
            )

    # TODO: For this request to work, you must replace "YOUR_FILE"
    #       with the location where the downloaded content should be written.
    # io.FileIO("YOUR_FILE", "wb")
    with open("captions.txt", "wb")  as fh:

        download = MediaIoBaseDownload(fh, request)
        complete = False
        while not complete:
            status, complete = download.next_chunk()
            print(status)

    return


def test():

    # seconds till next quota reset
    # midnight 2h till 2am
    assert time_till_quota_reset(datetime.datetime(2023, 4, 8, 0), 2) == 2 * 3600
    # 1am
    assert time_till_quota_reset(datetime.datetime(2023, 4, 8, 1), 2) == 3600
    # 2am
    assert time_till_quota_reset(datetime.datetime(2023, 4, 8, 2), 2) == 0
    # 3am
    assert time_till_quota_reset(datetime.datetime(2023, 4, 8, 3), 2) == 23 * 3600
    # 4am
    assert time_till_quota_reset(datetime.datetime(2023, 4, 8, 4), 2) == 22 * 3600
    # 23:00, midnight reset
    assert time_till_quota_reset(datetime.datetime(2023, 4, 8, 23), 0) == 3600


def make_parser():

    parser = argparse.ArgumentParser(
            description="Upload a file to youtube.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
            )

    parser.add_argument('--credintials-file', '-c',
            default=os.path.expanduser('~/.secrets/client_secrets.json'),
            dest="client_secrets_file",
            help="Process API key (what needs access to upload.)"),

    parser.add_argument('--token-file', '-t',
            default=os.path.expanduser('~/.secrets/oauth_token.json'),
            help="Auth token file. (permission from the destination account owner)")

    # find the test file
    ext = "mp4"
    veyepar_dir = os.path.expanduser('~/Videos/veyepar')
    test_dir = os.path.join(veyepar_dir, "test_client", "test_show", ext)
    test_file = os.path.join(test_dir, f"Lets_make_a_Test.{ext}")
    if not os.path.exists(test_file):
        # if we can't find a video to upload, upload this .py file!
        test_file = os.path.abspath(__file__)

    parser.add_argument('--pathname', '-f',
            default=test_file,
            # dest="filename",
            help='file to upload.')

    parser.add_argument('--delete',
                        help='existing youtube vid to delete.')

    parser.add_argument('--up-desc',
                        help='existing youtube vid to update desc.')

    parser.add_argument('--debug_mode', '-d', default=False,
            action='store_true',
            help='whether to drop to prompt after upload. default: False')

    return parser




def main():

    parser = make_parser()
    args = parser.parse_args()

    if args.up_desc:
        test_set_description( args )

    elif args.delete:
        # url = "http://youtu.be/C3U5G5uxgz4"
        url = args.delete
        test_delete(args, url)
    else:
        url = test_upload(args)
        # test_set_pub(args, "http://youtu.be/IdSelnHIxWY")
        # https://www.googleapis.com/youtube/v3/captions/H6hk0RhmAAs
        # test_caption( args.token_file, "H6hk0RhmAAs" )
        # test_set_unlisted( args.token_file, "hyd6MiWXSP4")
        # test_set_pub(args, 'http://youtu.be/tB3YtzAxFLo')
        # test_set_unlisted(args, "http://youtu.be/zN-drQny-m4")
        # test_set_unlisted(args, url)

if __name__ == '__main__':
    main()

