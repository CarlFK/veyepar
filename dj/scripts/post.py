#!/usr/bin/python

# posts to blip.tv, tweets it

from blip_uploader import Upload

import tweeter
import optparse
import re
import os

import pw
from process import process

from main.models import Show, Location, Episode, Raw_File, Cut_List

class post(process):

  ready_state = 3
  done_state = 4

  def process_ep(self, ep):
    print ep.id, ep.name
    loc = ep.location
    show = loc.show
    client = show.client

    # look for a thumb
    for cut in Cut_List.objects.filter(episode=ep).order_by('sequence'):
        basename = cut.raw_file.basename()        
        thumb=os.path.join(self.episode_dir, "%s.png"%(basename))
        if os.path.exists(thumb): break
    
    oggpathname = os.path.join( self.show_dir, "ogg", "%s.ogg"%(ep.slug) )
    description = "%s</br>\n</br>\n%s" % (ep.description, client.description)

    print description 

    meta = {
        'title': ep.name,
        'description': description,
        "topics": "%s, python, "%(client.name),
        "license": "13",
        "categories_id": "10",
        }

    print oggpathname, thumb
    print meta
    return 

    # blipurl = "http://carlfk.blip.tv/file/2213225"
    response = Upload("", pw.blip['user'], pw.blip['password'], oggpathname, meta, thumb)
    responsexml = response.read()
    blipurl = re.search("post_url>(.*)</post" ,responsexml).groups()[0]
    if blipurl:
        print blipurl
        prefix = "#%s VIDEO -" % show.client.name
        tweet = tweeter.notify(prefix, ep.name, blipurl)
        if "<id>" not in tweet: print tweet
        tweetid=re.search("<id>(.*)</id>" ,tweet).groups()[0]
        tweeturl="http://twitter.com/cfkarsten/status/%s"%(tweetid,)
        print tweeturl
        ep.comment += blipurl
        ep.state = self.done_state
    else:
        ep.comment += "upload failed\n"
    ep.save()

if __name__ == '__main__':
    p=post()
    p.main()

