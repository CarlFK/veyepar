# sync_rax.py
# syncs local files to rackspace cdn
# looks for files based on data in veyepar
# as in, if 12-34-56.dv is in raw_files, look for 12-34-56.ogv.
# no walking the directory tree looking for random files.

import os
import subprocess

from process import process
from main.models import Client, Show, Location, Episode, Raw_File

import rax_uploader
import gslevels

class SyncRax(process):

    def cdn_exists(self, show, dst):
        dst = os.path.join("veyepar",show.client.slug,show.slug,dst)
        return dst in self.names

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


    def rf_web(self, show, rf):
        """
        make a low bitrate version of the raw file 
        for previewing over the web
        """
        # base = os.path.join( "dv", rf.location.slug, rf.basename() )
        base = os.path.join( "dv", rf.location.slug, rf.filename )
        if self.options.verbose: print base

        # look for .webm on local file system
        # ext = os.path.splitext(rf.filename)[1]
        # rf = os.path.join(self.show_dir, base + ext)
        rf = os.path.join(self.show_dir, base )
        web = os.path.join(self.show_dir, base + ".webm")
        vb = "50k"
        # vb = "20k" # for SA
        if not os.path.exists(web):
            cmd = "melt {rf} -consumer avformat:{out} vb={vb} progress=1".format( rf=rf, vb=vb, out=web ).split()
            p=subprocess.Popen(cmd)
            p.wait()
            retcode=p.returncode
        
        web = base + ".webm"
        # Don't upload over phone.
        if not self.cdn_exists(show,web):
            self.file2cdn(show,web)


    def rf_audio_png(self, show, rf):
        # check for audio image
        rf_base = os.path.join( "dv", 
            rf.location.slug, rf.filename )

        png_base = os.path.join( "audio_png", "raw", 
            rf.location.slug, rf.filename + ".wav.png")
            # rf.location.slug, rf.basename() + "_audio.png")

        if not self.cdn_exists(show,png_base):
            print rf.filesize
            src = os.path.join(self.show_dir,rf_base)
            dst = os.path.join(self.show_dir,png_base)
            ret = self.mk_audio_png(src,dst)
            self.file2cdn(show,png_base)

   
    def raw_files(self, show):
        print "getting raw files..."
        rfs = Raw_File.objects.filter(show=show,)

	if self.options.day:
            rfs = rfs.filter(start__day=self.options.day)

	if self.options.room:
            loc = Location.objects.get(slug=self.options.room)
            rfs = rfs.filter(location = loc)

        # rfs = rfs.exclude(id=12212)
        rfs = rfs.exclude(filesize__lt=800000)

        # rfs = rfs.cut_list_set.filter(episode__id=8748)
        # rfs = rfs.cut_list_set.filter(episode__state=1)

        for rf in rfs:
            if self.options.verbose: print rf
            # self.rf_web(show, rf)
            self.rf_audio_png(show, rf)

    def sync_final(self,show,ep):
            base = os.path.join("webm", ep.slug + ".webm" )
            if not self.cdn_exists(show,base):
                 self.file2cdn(show,base)

    def sync_final_audio_png(self,show,ep):
        base = os.path.join("webm", ep.slug + "_audio.png" )
        if not self.cdn_exists(show,base):
             png_name = os.path.join( self.show_dir, base )
             ret = self.mk_audio_png(ep.public_url,png_name) 
             self.file2cdn(show,base)


    def sync_title_png(self,show,ep):
        base = os.path.join("titles", ep.slug + ".png" )
        p = u"base:{}".format(base)
        print(p)
        if not self.cdn_exists(show,base):
             png_name = os.path.join( self.show_dir, base )
             self.file2cdn(show,base)

    def episodes(self, show):
        eps = Episode.objects.filter(show=show)

	if self.options.day:
            eps = eps.filter(start__day=self.options.day)

	if self.options.room:
            loc = Location.objects.get(slug=self.options.room)
            eps = eps.filter(location = loc)

        # for ep in eps.filter(state=5):
            # self.sync_final(show,ep)
            # self.sync_final_audio_png(show,ep)
         
        # eps = eps.filter(state=4)
        for ep in eps:
            print(ep)
            # self.sync_title_png(show,ep)
            # import code; code.interact(local=locals())
            cls = ep.cut_list_set.all()
            for cl in cls:
                self.rf_web(show, cl.raw_file)


    def init_rax(self, show):
         user = show.client.rax_id
         bucket_id = show.client.bucket_id

         cf = rax_uploader.auth(user)

         print "cf.get_all_containers", cf.get_all_containers()
         
         container = cf.get_container(bucket_id)
         objects = container.get_objects()
         print "loading names..."
         self.names = {o.name for o in objects}
         print "loaded."

    def one_show(self, show):
        self.set_dirs(show)
        self.init_rax(show)

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


