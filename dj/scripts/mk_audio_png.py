#!/usr/bin/python

# mk_audio_png.py - visualize audio of final encode

import os

from process import process

import gslevels 

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

    def one_ext(self, ep, ext):
        base = os.path.join(ext, ep.slug + ".{}.png".format(ext) )
        png_name = os.path.join( self.show_dir, base )
        ret = self.mk_audio_png( ep.public_url, png_name ) 
        if ret and self.options.rsync:
            self.file2cdn( ep.show, base )

        return png_name
        
    
    def process_ep(self, ep):
        if self.options.verbose: print(ep.id, ep.name)

        self.files = []
        for ext in self.options.upload_formats:
            png_name = self.one_ext(ep, ext)
            self.files.append(png_name)

        ret = False # False else it will bump it +1)

        return ret

    def add_more_options(self, parser):
        parser.add_option('--rsync', action="store_true",
            help="upload to DS box.")

if __name__ == '__main__':
    p=mk_audio_png()
    p.main()

