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

class post(process):

  ready_state = 3

  def process_ep(self, ep):
    print ep.id, ep.name
    loc = ep.location
    show = loc.show
    client = show.client

    description = "%s</br>\n</br>\n%s" % (ep.description, client.description)

    blip_cli=blip_uploader.Blip_CLI()

    meta = {
        'title': ep.name,
        'description': description,
        }
    """
        # need to make a place for this stuff in the database.
        "topics": "%s, python, "%(client.name),
        "license": "13",
        "category_id": "10",
    """

    if self.options.topics:
        meta['topics'] = self.options.topics

    if self.options.license:
        meta['license'] = self.options.license

    if self.options.category:
        meta['category_id'] = self.options.category

    if self.options.hidden:
        meta['hidden'] = self.options.hidden

# look for a thumb
# TODO: thumb filename to the db.
    for cut in Cut_List.objects.filter(episode=ep).order_by('sequence'):
        basename = cut.raw_file.basename()        
        thumb=os.path.join(self.episode_dir, "%s.png"%(basename))
        if os.path.exists(thumb): break
    
# the blip api gets kinda funky around multiple uploads
# so no surprise the code is kinda funky.
    # files = [('','Source',src_pathname)]
    roles={
        'ogv':"Source", 
        'ogg':"Source", 
        'flv':"Web", 
        'mp4':"dvd", 
    }
    files = []
    exts = self.options.upload_formats.split()
    for i,ext in enumerate(exts):
        fileno=str(i) if i else ''
        role=roles.get(ext,'extra')
        src_pathname = os.path.join( self.show_dir, ext, "%s.%s"%(ep.slug,ext))
        files.append((fileno,role,src_pathname))

    blip_cli.debug = self.options.verbose

    # blip_ep=Blip_Ep()
    if self.options.test:
        print 'test mode:'
        print 'blip_cli.Upload( "", user, pw, files, meta, thumb)'
        print 'files %s' % files
        print 'meta %s' % meta
        print 'thumb %s' % thumb
        print
    
        blipcmd = "./blip_uploader.py --fileno %s --role %s --filename %s" % (files[0])
        blipcmd += " --thumb %s" % thumb 
        for i in meta.items():
            blipcmd += " --%s %s" % i 
        print blipcmd 

    else:
        response = blip_cli.Upload(
            "", pw.blip['user'], pw.blip['password'], files, meta, thumb)
        response_xml = response.read()
        if self.options.verbose: print response_xml
        blipurls = re.search("post_url>(.*)</post" ,response_xml).groups()
        if blipurls:
            blipurl=blipurls[0]
            print blipurl
            ep.comment += blipurl
            if pw.twit['user']:
                prefix = "%s #VIDEO -" % show.client.name
                tweet = tweeter.notify(prefix, ep.name, blipurl)
                print tweet
                if "<id>" not in tweet: print tweet
                tweetid=re.search("<id>(.*)</id>" ,tweet).groups()[0]
                tweeturl="http://twitter.com/cfkarsten/status/%s"%(tweetid,)
                print tweeturl
            ret=True
        else:
            if not self.options.verbose: print response_xml
            ep.comment += "upload failed\n%s\n" % response_xml
            ret=False
        ep.save()

        return ret

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

