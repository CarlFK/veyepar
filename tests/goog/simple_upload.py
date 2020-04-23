# simple_upload.py

import gflags
import httplib2
import os
import sys
import time

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run

FLAGS = gflags.FLAGS
gflags.DEFINE_string('file', 'foo.webm', 'Video file to upload')
gflags.DEFINE_string('title', 'Test title', 'Video title')
gflags.DEFINE_string('description', 'Test description', 'Video description')
gflags.DEFINE_string('category', 'VIDEO_CATEGORY_PEOPLE', 'Video category')
gflags.DEFINE_string('keywords', '', 'Video keywords, comma separated')
gflags.DEFINE_string('privacyStatus', 'PRIVACY_UNLISTED', 'Video privacy status')

def main(argv):

  # Let the gflags module process the command-line arguments
  try:
    argv = FLAGS(argv)
  except gflags.FlagsError as e:
    print( '{}\nUsage: {} ARGS\n{}'.format(e, argv[0], FLAGS) )
    sys.exit(1)

  print( FLAGS.file )

  if FLAGS.file is None or not os.path.exists(FLAGS.file):
    sys.exit('Please specify a valid file using the --file= parameter.')

  flow = flow_from_clientsecrets('v3_client_secrets.json',
      scope='https://www.googleapis.com/auth/youtube.upload')

  storage = Storage('ru-oauth2.dat')
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run(flow, storage)

  youtube = build('youtube', 'v3alpha',
      http=credentials.authorize(httplib2.Http()))

  insert_request = youtube.videos().insert(
    body = dict(
      snippet = dict(
        title=FLAGS.title,
        description=FLAGS.description,
        tags=FLAGS.keywords.split(','),
        categoryId=FLAGS.category
      ),
      status = dict(
        privacyStatus=FLAGS.privacyStatus
      )
    ),
    media_body = MediaFileUpload(FLAGS.file, chunksize=-1, resumable=True)
  )

  insert_request.headers['Slug'] = 'test_file'

  response = None
  backoff = 1
  while response is None:
    try:
      status, response = insert_request.next_chunk()
      print( '"{}" (video ID: {}) was successfully uploaded.'.format(
          FLAGS.title, response['id']))

    except HttpError as e:
      print( 'An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))
      if e.resp.status in [500, 502, 503, 504]:
        backoff *= 2
        if backoff > 900:
          exit('No longer attempting to retry.')
        print( 'Sleeping %d seconds and then retrying ...' % (backoff))
        time.sleep(backoff)

if __name__ == '__main__':
  main(sys.argv)
