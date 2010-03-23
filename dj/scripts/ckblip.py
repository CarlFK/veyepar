#!/usr/bin/python

# ckblip.py
# checks metadata on blib
# like 'is there a flash version?'

import os

import blip_uploader

from process import process

from main.models import Episode

class ckblip(process):

  ready_state = None # check all episodes, don't bump state

  def process_ep(self, ep):
    # if self.options.verbose: print ep.id, ep.name


    """
    ext='flac'
    out_pathname = os.path.join(
        self.show_dir, ext, "%s.%s"%(ep.slug,ext))
    if ep.state>2 and not os.path.exists(out_pathname): print ep.id, 
    return True
    """

    blip_cli=blip_uploader.Blip_CLI()

    if ep.target:
        video_id = ep.target
        if self.options.verbose: print ep.id, ep.name, ep.target

        blip_cli.debug = self.options.verbose
        # blip_cli.List_VideoMeta(video_id)
        xml_code = blip_cli.Get_VideoMeta(video_id)
        if self.options.verbose: print xml_code
        info = blip_cli.Parse_VideoMeta(xml_code)
        flv=None
        for content in info['contents']:
            if self.options.verbose: 
                print content['role'], content['type'],
            if content['type'] == 'video/x-flv':
                flv=True
        if not flv: 
            print ep.id,
            # print ep.target, "http://blip.tv/file/%s" % ep.target, ep.name, ep.id

    # ep.save()

    ret = True
    return ret

  def add_more_options(self, parser):
        parser.add_option('--rating', 
            help="TV rating")
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
    p=ckblip()
    p.main()

