#!/usr/bin/python

# mk_audio_png.py - mass fix some goof


import os

import gslevels 

from process import process

from main.models import Show, Location, Episode, Raw_File, Cut_List

class mk_audio_png(process):

    ready_state = None

    def mk_audio_png(self,src,png_name):
        """ 
        make audio png from source, 
        src can be http:// or file://
        dst is the local fs.
        """
        p = gslevels.Make_png()
        p.location = src
        p.verbose = self.options.verbose
        p.setup()
        p.start()
        ret = p.mk_png(png_name)

        return ret

    def process_ep(self, ep):
        if self.options.verbose: print ep.id, ep.name

        ext = "webm"
        base = os.path.join(ext, ep.slug + ".{}.png".format(ext) )
        png_name = os.path.join( self.show_dir, base )
        ret = self.mk_audio_png( ep.public_url, png_name ) 
        self.file2cdn( ep.show, base )
        
        ep.save()

        ret = False # False else it will bump it +1)

        self.ret = ret
        return ret

if __name__ == '__main__':
    p=fix()
    p.main()

