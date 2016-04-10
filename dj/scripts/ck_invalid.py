#!/usr/bin/python

# ck_invalid.py
# looks for a big "INVALID" video 
# which is what melt does when things are broken

# todo: look for silence too.  
# not sure what that algorithem will look like, 
# so this can wait till I have a problem

import os
import gslevels
from . import gsocr

from process import process

class ckbroke(process):

    ready_state = 3

    def process_ep(self, ep):
        exts = self.options.upload_formats
        for ext in exts:
            src_pathname = os.path.join( self.show_dir, ext, 
                "%s.%s"%(ep.slug,ext))

            p=gsocr.Main(src_pathname)
            # gocr -s 40 -C A-Z ~/shot0001.png INVALID 
            p.gocr_cmd = ['gocr', '-', '-s', '40', '-C', 'A-Z']
            dictionary = ["INVALID"]
            p.dictionaries=[dictionary]
            # p.frame=30*5 # start 5 seconds into it (past the title)
            p.seek_sec = 1
            
            if self.options.verbose: print("checking ", ext)

            gsocr.gtk.main()
            print(p.words)
            if p.words: ## ["INVALID"] is kinda the only thing it can be
                print(ep.id, ep.name)
                print(p.words)
                ep.name = "INVALID " + ep.name
                ep.state = -1
                ep.save()
                ret=False
            else:
                # return True to bump state
                # assuming we are not --force-ing the check 
                ret=self.options.push

        return ret

    def add_more_options(self, parser):
        parser.add_option('--push', 
            help="Push episode past review step if it passes check.")


if __name__ == '__main__':
    p=ckbroke()
    p.main()

