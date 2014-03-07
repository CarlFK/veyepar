# sync_rax.py
# syncs local files to rackspace cdn
# looks for files based on data in veyepar
# as in, if 12-34-56.dv is in raw_files, look for 12-34-56.ogv.
# no walking the directory tree looking for random files.

import os

from process import process
from main.models import Client, Show, Episode, Raw_File

import rax_uploader


class SyncRax(process):

    def one_file(self, show, src, dst=None):
        """
        src is relitive to the show dir.
        src and dst get filled to full paths.
        Check to see if src exists,
        if it does, try to upload it to cdn
        (rax_uploader will skip if same file exists).
        """
        if dst is None: dst = src

        src = os.path.join(self.show_dir,src)
        dst = os.path.join("veyepar",show.client.slug,show.slug,dst)

        if os.path.exists(src):
            print "uploading:", src

            u = rax_uploader.Uploader()

            u.user = self.options.cloud_user
            u.bucket_id = self.options.rax_bucket
            u.pathname = src
            u.key_id = dst

            ret = u.upload()

        return

    def raw_files(self, show):
        for rf in Raw_File.objects.filter(show=show):
            base = os.path.join(rf.location.slug, rf.basename() + "_audio.png")
            src = os.path.join("audio_png", "dv", base)
            self.one_file(show,src)

            base = os.path.join(rf.location.slug, rf.basename() + ".ogv")
            src = os.path.join("dv", base)
            self.one_file(show,src)
              

    def episodes(self, show):
        for ep in Episode.objects.filter(show=show):
            base = ep.slug + ".webm"
            src = os.path.join("webm", base)
            self.one_file(show,src)

    def one_show(self, show):
        self.set_dirs(show)

        self.raw_files(show)
        self.episodes(show)

    def work(self):
        """
        find and process show
        """
        if self.options.client and self.options.show:
            client = Client.objects.get(slug=self.options.client)
            show = Show.objects.get(client=client, slug=self.options.show)
            self.one_show(show)

        return

if __name__=='__main__': 
    p=SyncRax()
    p.main()

