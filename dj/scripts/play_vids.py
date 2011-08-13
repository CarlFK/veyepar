#!/usr/bin/python

# play_vids.py
# plays the encoded videos 
# written for run_test.py

import os, subprocess

from process import process

class play_vids(process):

    ready_state = 3

    def process_ep(self, ep):
        exts = self.options.upload_formats
        if self.options.verbose: print exts
        for ext in exts:
            filename = "%s.%s"%(ep.slug,ext)
            pathname = os.path.join( self.show_dir, ext, filename )
            if self.options.verbose: print pathname
            # cmd = "mplayer -speed 4 -osdlevel 3 %s"  % (pathname)
            parms = {'id':ep.id, 
                'filename':filename, 'pathname':pathname, 
                'speed':4}
            markup = "id:%(id)s #timecode#\n%(filename)s\n" % parms,
            cmd = ["melt", pathname,
                "meta.attr.titles=1", 
                "meta.attr.titles.markup=%s" % markup,
                "-attach", "data_show", "dynamic=1", ]

            if self.options.verbose: print cmd
            if self.options.test:
                print "test mode, not running command."
            else:
                p=subprocess.Popen(cmd).wait()


if __name__ == '__main__':
    p=play_vids()
    p.main()

