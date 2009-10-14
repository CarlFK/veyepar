#!/usr/bin/python

# posts to blip.tv, tweets it

import blip_uploader

import tweeter
import optparse
import re
import os

import pw
from process import process

from main.models import Show, Location, Episode, Raw_File, Cut_List

"""
class Blip_Ep(blip_uploader.Blip):

    def progress(self, current, total):
        " ""
        Displaies upload percent done, bytes sent, total bytes.
        " ""
        sys.stdout.write('\r%3i%%  %s of %s bytes'
            % (100*current/total, current, total))
"""

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

    blip_cli=blip_uploader.Blip_CLI()

    meta = {
        'title': ep.name,
        'description': description,
        }
    """
        # need to make a place for this stuff in the database.
        "topics": "%s, python, "%(client.name),
        "license": "13",
        "categories_id": "10",
    """

    if self.options.topics:
        meta['topics'] = self.options.topics

    if self.options.license:
        meta['license'] = self.options.license

    if self.options.category:
        meta['categorie_id'] = self.options.category

    if self.options.hidden:
        meta['hidden'] = self.options.hidden

    print oggpathname, thumb

    # blip_ep=Blip_Ep()
    if self.options.test:
        print 'test mode:'
        print 'blip_cli.Upload( "", user, pw, oggpathname, meta, thumb)'
        print 'oggpathname %s' % oggpathname
        print 'meta %s' % meta
        print 'thumb %s' % thumb
        print
    else:
        response = blip_cli.Upload(
            "", pw.blip['user'], pw.blip['password'], oggpathname, meta, thumb)
        responsexml = response.read()
        blipurl = re.search("post_url>(.*)</post" ,responsexml).groups()[0]
        if blipurl:
            print blipurl
            prefix = "#%s VIDEO -" % show.client.name
            tweet = tweeter.notify(prefix, ep.name, blipurl)
            print tweet
            if "<id>" not in tweet: print tweet
            tweetid=re.search("<id>(.*)</id>" ,tweet).groups()[0]
            tweeturl="http://twitter.com/cfkarsten/status/%s"%(tweetid,)
            print tweeturl
            ep.comment += blipurl
            ep.state = self.done_state
        else:
            ep.comment += "upload failed\n"
        ep.save()

  def add_more_options(self, parser):
        parser.add_option('-T', '--topics',
            help="list of topics (user defined)")
        parser.add_option('-L', '--license',
            help="13 is Creative Commons Attribution-NC-ShareAlike 3.0\n"
            "'./blip_uploader.py -L list' to see full list" )
        parser.add_option('-C', '--category',
            help = "'./blip_uploader.py -C list' to see full list" )
        parser.add_option('--hidden',
            help="availability on blip.tv, 0=Available, 1=Hidden, 2=Available to family, 4=Available to friends/family.")


if __name__ == '__main__':
    p=post()
    p.main()

