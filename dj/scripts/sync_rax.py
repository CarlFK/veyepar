# sync_rax.py
# syncs local files to rackspace cdn
# looks for files based on data in veyepar
# as in, if 12-34-56.dv is in raw_files, look for 12-34-56.ogv.
# no walking the directory tree looking for random files.

import os
import subprocess

from process import process
from main.models import Client, Show, Location, Episode, \
  Raw_File, Cut_List

import swift_uploader as rax_uploader
import gslevels

class SyncRax(process):

    def cdn_exists(self, show, dst):
        dst = os.path.join("veyepar",show.client.slug,show.slug,dst)
        # import code; code.interact(local=locals())

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
        if self.options.verbose: print(base)

        # look for .webm on local file system
        # ext = os.path.splitext(rf.filename)[1]
        # rf = os.path.join(self.show_dir, base + ext)
        rf = os.path.join(self.show_dir, base )
        web = os.path.join(self.show_dir, base + ".webm")
        vb = "50k"
        # vb = "20k" # for SA
        if not os.path.exists(web):
            cmd = ["melt", rf, "meta.attr.titles=1", "meta.attr.titles.markup=#timecode#", "-attach", "data_show", "dynamic=1", "-consumer", "avformat:"+web, "vb="+vb, "progress=1"]
            # cmd = "melt {rf} -consumer avformat:{out} vb={vb} progress=1".format( rf=rf, vb=vb, out=web ).split()
            p=subprocess.Popen(cmd)
            p.wait()
            retcode=p.returncode
        
        web = base + ".webm"
        if not self.cdn_exists(show,web):
            self.file2cdn(show,web)


    def rf_audio_png(self, show, rf):
        rf_base = os.path.join( "dv", 
            rf.location.slug, rf.filename )

        png_base = os.path.join( "audio_png", "raw", 
            rf.location.slug, rf.filename + ".wav.png")

        if not self.cdn_exists(show,png_base):
            print(rf.filesize)
            src = os.path.join(self.show_dir,rf_base)
            dst = os.path.join(self.show_dir,png_base)
            ret = self.mk_audio_png(src,dst)
            self.file2cdn(show,png_base)

   
    def raw_files(self, show):
        print("getting raw files...")
        rfs = Raw_File.objects.filter(show=show,)

        if self.options.day:
            rfs = rfs.filter(start__day=self.options.day)

        if self.options.room:
            loc = Location.objects.get(slug=self.options.room)
            rfs = rfs.filter(location = loc)

        # rfs = rfs.exclude(id=12212)
        # rfs = rfs.exclude(filesize__lt=800000)

        if self.args:
            eps = Episode.objects.filter(id__in=self.args)
            cls = Cut_List.objects.filter(episode__in=eps)
            rfs = rfs.filter(cut_list__in=cls).distinct()

        for rf in rfs:
            if self.options.verbose: print(rf)
            self.rf_web(show, rf)
            # self.rf_audio_png(show, rf)

    def sync_final(self,show,ep):
        ext = "mp4"
        base = os.path.join( ext, "{}.{}".format(ep.slug, ext) )
        # if not self.cdn_exists(show,base):
        self.file2cdn(show,base)

    def sync_final_audio_png(self,show,ep):
        ext = "webm"
        base = os.path.join(ext, ep.slug + ".{}.png".format(ext) )
        if not self.cdn_exists(show,base):
             png_name = os.path.join( self.show_dir, base )
             ret = self.mk_audio_png( ep.public_url, png_name ) 
             self.file2cdn(show,base)

    def cut_list(self,show,ep):
        cls = ep.cut_list_set.all()
        for cl in cls:
            self.rf_web(show, cl.raw_file)


    def sync_title_png(self,show,ep):
        base = os.path.join("titles", ep.slug + ".png" )
        if not self.cdn_exists(show,base):
            self.file2cdn(show,base)

    def mlt(self,show,ep):
        # put whatever is found into target/mlt
        # kinda wonky, but not sure how to handle this yet.

        mlt = os.path.join("mlt", ep.slug + ".mlt" )

        custom_mlt = os.path.join("custom", ep.slug + ".mlt" )
        if os.path.exists( os.path.join(self.show_dir, custom_mlt )):
            src = custom_mlt
        else:
            src = mlt

        self.file2cdn(show,src,mlt)

    def episodes(self, show):
        eps = Episode.objects.filter(show=show)

        if self.options.day:
            eps = eps.filter(start__day=self.options.day)

        if self.options.room:
            loc = Location.objects.get(slug=self.options.room)
            eps = eps.filter(location = loc)

        if self.args:
            eps = eps.filter(id__in=self.args)

        # eps = eps.filter(state=3)

        for ep in eps:
            print(ep)
            self.sync_title_png(show,ep)
            # self.cut_list(show,ep)
            self.mlt(show,ep)
            # self.sync_final(show,ep)
            # self.sync_final_audio_png(show,ep)

    def show_assets(self,show):
        foot_img = show.client.credits
        base = os.path.join("assets", foot_img )
        self.file2cdn(show,base)

    def init_rax(self, show):
         user = show.client.rax_id
         bucket_id = show.client.bucket_id

         conn = rax_uploader.auth(user)

         # print("cf.get_all_containers", cf.get_all_containers())
         
         container = conn.get_container(bucket_id)
         objects = container[1]

         """
         for data in conn.get_container(container_name)[1]:
                     print( '{0}\t{1}\t{2}'.format(data['name'], data['bytes'], data['last_modified']))
         """

         # objects = container.get_objects()
         print("loading names...")
         self.names = {o['name'] for o in objects}
         print("loaded.")

    def one_show(self, show):
        self.set_dirs(show)
        self.init_rax(show)

        # self.show_assets(show)
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


