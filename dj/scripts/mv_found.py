#!/usr/bin/python

# mv_found - moves the mp4s we know of to ./found
# so we can see what is left over

import os

from process import process

# from main.models import Show, Location, Episode, Raw_File, Cut_List
from main.models import Episode

class mv(process):

    # this will bump everything past the review1 step
    ready_state = None

    def process_ep(self, ep):
        if self.options.verbose: print(ep.id, ep.name)
        file_name = ep.slug + ".mp4"
        src = os.path.join( self.show_dir, "mp4", file_name )
        dst = os.path.join( self.show_dir, "mp4", "found", file_name )
        self.run_cmd( ['mv', src, dst])

        # ret = True

        # ep.save()

        # return ret

if __name__ == '__main__':
    p=mv()
    p.main()

