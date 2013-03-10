from steve.restapi import API, get_content
from steve.richardapi import create_video

import datetime

import pw

host = pw.richard["test"]  # keys: user, host, api_key

pyvideo_endpoint = 'http://{hostname}/api/v1'.format(
        hostname = host['host'])

video_data = {
            'id': 1101,
            'category': 'ChiPy',
            'state': 1,
            'title': 'Test video title',
            'speakers': ['Jimmy Discotheque'],
            'language': 'English',
            'added': datetime.datetime.now().isoformat()
        }

vid = create_video( pyvideo_endpoint, 
        host['user'], host['api_key'], video_data)

vid_id = "2261"
# this line errors
old_video = api_video(vid_id).get()
