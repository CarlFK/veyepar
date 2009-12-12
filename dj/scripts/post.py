#!/usr/bin/python

# posts to blip.tv, tweets it

import blip_uploader

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
    show = ep.show
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
    if self.options.update:
        # http://blip.tv/file/2873957
        # video_id = ep.comment.replace('http://blip.tv/file/','')
        video_id = ep.comment.strip(' \n')[-7:]
        print ep.name, video_id
    else:
        # create new episode
        video_id = ''

    if self.options.topics:
        meta['topics'] = self.options.topics

    if self.options.license:
        meta['license'] = self.options.license

    if self.options.category:
        meta['category_id'] = self.options.category

    if self.options.hidden:
        meta['hidden'] = self.options.hidden

    thumb = ep.thumbnail
    
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
# pull dv from the list
    exts = [e for e in exts if e != 'dv']
    for i,ext in enumerate(exts):
        fileno=str(i) if i else ''
        role=roles.get(ext,'extra')
        src_pathname = os.path.join( self.show_dir, ext, "%s.%s"%(ep.slug,ext))
        files.append((fileno,role,src_pathname))

    blip_cli.debug = self.options.verbose

    # blip_ep=Blip_Ep()
    if self.options.test:
        print 'test mode:'
        print 'blip_cli.Upload( video_id, user, pw, files, meta, thumb)'
        print video_id
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
            video_id, pw.blip['user'], pw.blip['password'], files, meta, thumb)
        response_xml = response.read()
        if self.options.verbose: print response_xml
        blip_urls = re.search("post_url>(.*)</post" ,response_xml).groups()
        if blip_urls:
            blip_url=blip_urls[0]
            blip_id=blip_url[-7:]
            if self.options.verbose:
                print blip_url, blip_id
            ep.target = blip_id
            ep.comment += blip_url
            self.log_info(blip_url)
            ret=True
        else:
            if not self.options.verbose: print response_xml
            ep.comment += "upload failed\n%s\n" % response_xml
            ret=False
        ep.save()

        return ret

  def add_more_options(self, parser):
        parser.add_option('-u', '--update', action='store_true',
            help="update existing episode")
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

