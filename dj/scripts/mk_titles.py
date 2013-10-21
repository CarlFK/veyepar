#!/usr/bin/python

# creates svg titles for all the episodes
# used to preview the title slides, 
# enc.py will re-run the same code.

import os
import subprocess

from enc import enc

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

class mk_title(enc):

    ready_state = None

    def rsync(self, ep, files):


        # Ryans data center box, 
        # veyepar user and /home dir
        # uses ssh keys from local box 

        # user="veyepar"
        # host =  'nextdayvideo.com'
        host = self.options.cloud_host
        user = self.options.cloud_user

        dest_host = '%s@%s' % (user,host)

        dest_show_path = "/home/%s/Videos/veyepar/%s/%s" % (
                user, ep.show.client.slug, ep.show.slug, )

        for f in files:

            dest_path = "%s/%s" % ( dest_show_path, f['dest_tail'] )

            dest = "%s:%s" %( dest_host, dest_path )

            cmd = ['ssh', '-p', '222', dest_host, 'mkdir', '-p', dest_path ]
            self.run_cmd(cmd)

            cmd = ['rsync',  
                    '-rtvP', 
                    '-e', 'ssh -p 222',
                    f['src_pathname'], dest ]
            self.run_cmd(cmd)

        return 

    def process_ep(self, episode):

        title_img=self.mk_title(episode)

        if self.options.rsync:
            svg = title_img[:-3] + "svg"
            files = [{'src_pathname':title_img,'dest_tail':'titles'}, 
                     {'src_pathname':svg,      'dest_tail':'titles'}] 
            self.rsync(episode, files)

        return False # not sure what this means.. we don't bump state

    def add_more_options(self, parser):
        parser.add_option('--rsync', action="store_true",
            help="upload to DS box.")

if __name__ == '__main__':
    p=mk_title()
    p.main()

