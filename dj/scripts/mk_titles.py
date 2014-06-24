#!/usr/bin/python

# creates svg titles for all the episodes
# used to preview the title slides, 
# enc.py will re-run the same code.

import os
import subprocess

import rax_uploader

from enc import enc

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

class mk_title(enc):

    ready_state = None

    def file2cdn(self, show, src, dst=None):
        """
        src is relitive to the show dir.
        src and dst get filled to full paths.
        Check to see if src exists,
        if it does, try to upload it to cdn
        (rax_uploader will skip if same file exists).
        """
        print "checking:", src 

        if dst is None: dst = src 

        src = os.path.join(self.show_dir,src)
        dst = os.path.join("veyepar",show.client.slug,show.slug,dst)

        if os.path.exists(src):

            u = rax_uploader.Uploader()

            u.user = self.options.cloud_user
            u.bucket_id = self.options.rax_bucket
            u.pathname = src 
            u.key_id = dst 

            ret = u.upload()

    def process_ep(self, episode):

        title_img=self.mk_title(episode)

        self.file2cdn(episode.show, "titles/%s.svg" % (episode.slug))
        self.file2cdn(episode.show, "titles/%s.png" % (episode.slug))

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

