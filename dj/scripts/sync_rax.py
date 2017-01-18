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

    def mk_audio_png(self, src, png_name):
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

    def rf_web(self, show, rf):
        """
        make a low bitrate version of the raw file
        for previewing over the web
        """

        for ext in self.options.upload_formats:

            base = os.path.join( "dv", rf.location.slug, rf.filename )
            if self.options.verbose: print(base)

            rf = os.path.join(self.show_dir, base)
            low = "{base}.{ext}".format(base=base, ext=ext)
            out = os.path.join(self.show_dir, low)

            # look for low on local file system
            vb = "50k"
            # vb = "20k" # for SA
            if not os.path.exists(out):

                # symaphore? so a 2nd process doesn't do this file too
                cmd = ['touch', out]
                self.run_cmd(cmd)

                tmp = "{out}.tmp".format(out=out)

                cmd = ["melt", rf,
                        "meta.attr.titles=1",
                        "meta.attr.titles.markup=#timecode#",
                        "-attach", "data_show", "dynamic=1",
                    "-consumer", "avformat:"+tmp,
                        "vb="+vb, "progress=1",
                        "acodec=aac", "vcodec=libx264", "ab=50k",
                        "preset=ultrafast", "progress=1",
                        "movflags=+faststart", ]
                # , "threads=6"]
                        # "properties=x264-medium",
                p=subprocess.Popen(cmd)
                p.wait()
                retcode=p.returncode

                cmd = ['mv', tmp, out]
                self.run_cmd(cmd)

            if self.options.rsync:
                if not self.cdn_exists(show,low):
                    # raw file (huge!!!)
                    ### self.file2cdn(show,base)
                    self.file2cdn(show,low)


    def rf_audio_png(self, show, rf):

        rf_tail = os.path.join( "dv", rf.location.slug, rf.filename )
        png_tail = "{rf_tail}.wav.png".format(rf_tail=rf_tail)

        src = os.path.join(self.show_dir,rf_tail)
        dst = os.path.join(self.show_dir,png_tail)

        if not os.path.exists(dst) or self.options.force:
            ret = self.mk_audio_png(src,dst)

        if self.options.rsync and (
                not self.cdn_exists(show,png_tail) or self.options.force):
            print("rf.filesize:{}".format(rf.filesize))
            self.file2cdn(show,png_tail)


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
        # rfs = rfs.exclude(filename="2016-07-30/12_55_51.ts")

        if self.args:
            """
            eps = Episode.objects.filter(id__in=self.args)
            cls = Cut_List.objects.filter(episode__in=eps)
            rfs = rfs.filter(cut_list__in=cls).distinct()
            """
            rfs = rfs.filter(filename__in=self.args)


        for rf in rfs:
            if self.options.verbose: print(rf)
            if self.options.low:
                self.rf_web(show, rf)
            if self.options.audio_viz:
                self.rf_audio_png(show, rf)

    def sync_final(self,show,ep):
        for ext in self.options.upload_formats:
            base = os.path.join( ext, "{}.{}".format(ep.slug, ext) )
            # if not self.cdn_exists(show,base):
            self.file2cdn(show,base)

    def sync_final_audio_png(self,show,ep):

        for ext in self.options.upload_formats:

            src_tail = os.path.join(ext, ep.slug + ".{}".format(ext) )
            png_tail = "{src_tail}.wav.png".format(src_tail=src_tail)

            src_name = os.path.join(self.show_dir, src_tail)
            png_name = os.path.join(self.show_dir, png_tail)

            if os.path.exists(src_name):

                if not os.path.exists(png_name):
                    # self.mk_audio_png(ep.public_url, png_name)
                    self.mk_audio_png(src_name, png_name)

                if self.options.rsync:
                    self.file2cdn(show, png_tail)

            else:
                if self.options.verbose:
                    print("src not found: {src_name}".format(
                        src_name=src_name))


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

            if self.options.assets and self.options.rsync:
                self.sync_title_png(show, ep)
                self.mlt(show,ep)

            if self.options.rsync:
                self.sync_final(show, ep)

            if self.options.audio_viz:
                self.sync_final_audio_png(show,ep)

            if self.options.raw:
                self.cut_list(show,ep)

            # if ep.state>1:
            #    return


    def show_assets(self,show):
        foot_img = show.client.credits
        base = os.path.join("assets", foot_img )
        self.file2cdn(show,base)

    def init_rax(self, show):
         user = show.client.rax_id
         bucket_id = show.client.bucket_id

         u = rax_uploader.Uploader()
         u.user = show.client.rax_id
         conn = u.auth()

         # print("cf.get_all_containers", cf.get_all_containers())

         print(bucket_id)
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

        if self.options.rsync:
            self.init_rax(show)

        if self.options.assets:
            self.show_assets(show)
        if self.options.raw:
            self.raw_files(show)
        if self.options.cooked:
            self.episodes(show)


    def work(self):
        """
        find and process show
        """
        if self.options.client:
            client = Client.objects.get(slug=self.options.client)
            show = Show.objects.get(
                    client=client, slug=self.options.show)
        else:
            show = Show.objects.get(slug=self.options.show)

        self.one_show(show)

        return

    def add_more_options(self, parser):
        parser.add_option('--assets', action="store_true",
           help="synd asset files.")
        parser.add_option('--raw', action="store_true",
           help="process raw files.")
        parser.add_option('--low', action="store_true",
           help="make low quality files.")
        parser.add_option('--audio-viz', action="store_true",
           help="make audio visualization files.")
        parser.add_option('--cooked', action="store_true",
           help="process cooked files.")
        parser.add_option('--rsync', action="store_true",
            help="upload to DS box.")

if __name__=='__main__':
    p=SyncRax()
    p.main()


