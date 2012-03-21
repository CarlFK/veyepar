#!/usr/bin/python

# gets public URLs from PyVideo.org

import process
from main.models import Location, Episode, Raw_File, Cut_List, Client, Show
import urllib, urllib2
import json

class get_pub_urls(process.process):

    def process_ep(self, episode):
        if episode.host_url and\
                ((not episode.public_url) or self.options.update):
            print episode.host_url
            # urllib.urlencode({'host_url':'http://blip.tv/file/4881071'})
            # http://pyvideo.org/api/1.0/videos/urlforsource?
            # {"source_url": "http://pyvideo.org/video/644/introduction-to-pdb"}
            qp = urllib.urlencode({'host_url':episode.host_url})
            url = "http://pyvideo.org/api/1.0/videos/urlforsource?%s" % qp
            req = urllib2.Request(url)
            req.add_header('Accept', 'application/json')
            response = urllib2.urlopen(req)
            j = response.read()
            r = json.loads(j)
            episode.public_url = r['source_url']
            episode.save()


    def add_more_options(self, parser):
        parser.add_option('-u', '--update', action="store_true", 
          help='check for updated PVO urls (takes longer)' )


if __name__=='__main__': 
    p=get_pub_urls()
    p.main()

