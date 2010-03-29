#!/usr/bin/python

# ckblip.py
# checks metadata on blib
# like 'is there a flash version?'
# or 'if a format is not on blip, is it local?'
# and maybe upload it.


import os

import blip_uploader

from process import process

from main.models import Episode

class ckblip(process):

  def process_ep(self, ep):
    if self.options.verbose: print ep.id, ep.name, ep.target

    if ep.state == -1: return 
    """
    ext='flac'
    out_pathname = os.path.join(
        self.show_dir, ext, "%s.%s"%(ep.slug,ext))
    if ep.state>2 and not os.path.exists(out_pathname): print ep.id, 
    return True
    """

    types = (('ogv','video/ogg'),
             ('flv','video/x-flv'),
             ('m4v','video/x-m4v'),
             ('mp3','audio/mpeg'),)

    if ep.target:
        
        blip_cli=blip_uploader.Blip_CLI()
        blip_cli.debug = self.options.verbose

        xml_code = blip_cli.Get_VideoMeta(ep.target)
        if self.options.verbose: print xml_code
        meta = blip_cli.Parse_VideoMeta(xml_code)
        types_on_blip = [ content['type'] for content in meta['contents']]

    else:
        types_on_blip = []
        
    if self.options.verbose: 
        print types_on_blip
# [u'video/ogg', u'audio/mpeg', u'video/x-flv', u'video/x-m4v']
        
    for t in types:
        if t[1] not in types_on_blip:
            pathname = os.path.join(
                    self.show_dir, t[0], "%s.%s"%(ep.slug,t[0]))
            if not os.path.exists(pathname):
                print ep.id, t, pathname

        # print ep.target, "http://blip.tv/file/%s" % ep.target, ep.name, ep.id

    # ep.save()

    ret = True
    return ret


if __name__ == '__main__':
    p=ckblip()
    p.main()

