# sync_rax.py
# syncs local files to rackspace cdn
# looks for files based on data in veyepar
# as in, if 12-34-56.dv is in raw_files, look for 12-34-56.ogv.
# no walking the directory tree looking for random files.

import os

from process import process
from main.models import Client, Show, Episode, Raw_File

import rax_uploader
import gslevels

class SyncRax(process):

    def cdn_exists(self, show, dst):
        dst = os.path.join("veyepar",show.client.slug,show.slug,dst)
        return dst in self.names


    def cdn_send(self, show, src, dst=None):
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

        print "checking:", src
        if os.path.exists(src):

            print "off to rax_uploader.Uploader()..."

            u = rax_uploader.Uploader()

            u.user = self.options.cloud_user
            u.bucket_id = self.options.rax_bucket
            u.pathname = src
            u.key_id = dst

            ret = u.upload()

        return

    def mk_audio_png(self,src,png_name):
        """ 
        make audio png from source, 
        src can be http:// or file://
        dst is the local fs.
        """
        p = gslevels.Make_png()
        p.uri = src
        p.verbose = self.options.verbose
        p.setup()
        p.start()
        ret = p.mk_png(png_name)

        return ret

    def mk_final_audio_png(self,ep):
        """ whack to catch up 
        if the ep doen't have a png on the local fs, 
        make it from the public webm.
        """
        png_name = os.path.join(
                    self.show_dir,"webm", ep.slug + "_audio.png")
        # if not os.path.exists(png_name):
        ret = self.mk_audio_png(ep.public_url,png_name)

        return ret


    def rf_ogv(self, show, rf):
        # look for .ogv
        base = os.path.join(
                "dv", rf.location.slug, rf.basename() + ".ogv")
        if not self.cdn_exists(show,base):
            self.cdn_send(show,base)


    def rf_audio_png(self, show, rf):
        # check for audio image
        rf_base = os.path.join( "dv", 
            rf.location.slug, rf.filename )

        png_base = os.path.join( "audio_png", "dv", 
            rf.location.slug, rf.basename() + "_audio.png")

        if not self.cdn_exists(show,png):
            print rf.filesize
            src = os.path.join(self.show_dir,rf_base)
            dst = os.path.join(self.show_dir,png_base)
            ret = self.mk_audio_png(src,dst)
            self.cdn_send(show,png_base)

   
    def raw_files(self, show):
        print "getting raw files..."
        for rf in Raw_File.objects.filter(show=show):

            self.rf_ogv(show, rf)
            self.rf_audio_png(show, rf)

    def sync_final(self,show,ep):
            base = os.path.join("webm", ep.slug + ".webm" )
            if not self.cdn_exists(show,base):
                self.cdn_send(show,base)

    def sync_final_audio_png(self,show,ep):
            base = os.path.join("webm", ep.slug + "_audio.png" )
            if not self.cdn_exists(show,base):
                 png_name = os.path.join( self.show_dir, base )
                 ret = self.mk_audio_png(ep.public_url,png_name) 
                 self.cdn_send(show,base)

    def episodes(self, show):
        for ep in Episode.objects.filter(show=show, state=5):
            self.sync_final(show,ep)
            self.sync_final_audio_png(show,ep)

    def init_rax(self):
         user = self.options.cloud_user
         cf = rax_uploader.auth(user)
         bucket_id = self.options.rax_bucket
         container = cf.get_container(bucket_id)
         objects = container.get_objects()
         print "loading names..."
         self.names = {o.name for o in objects}
         print "loaded."

    def one_show(self, show):
        self.init_rax()
        self.set_dirs(show)

        self.raw_files(show)
        # self.episodes(show)


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


