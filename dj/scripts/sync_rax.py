# sync_rax.py
# syncs local files to rackspace cdn
# looks for files based on data in veyepar
# as in, if 12-34-56.dv is in raw_files, look for 12-34-56.ogv.
# no walking the directory tree looking for random files.

import os
import subprocess

from pprint import pprint
from process import process
from main.models import Client, Show, Location, Episode, \
  Raw_File, Cut_List

# import swift_uploader as rax_uploader
import gslevels

class SyncRax(process):

    def cdn_exists(self, show, dst):
        # need to figure out how to get a list of names from ... rsync?
        return False
        dst = os.path.join("veyepar",show.client.slug,show.slug,dst)
        # import code; code.interact(local=locals())

        return dst in self.names

    def mk_audio(self, src, aac_name):
        """
        make audio from source,
        src can be http:// or file://
        dst is the local fs.
        for f in *.ts; do time gst-launch-1.0 -e filesrc location=$f ! tsdemux ! mpegaudioparse ! filesink location=$f.mp2; done
        """
        cmd = ['gst-launch-1.0', '-e',
                'filesrc', 'location={}'.format(src), '!',
                'tsdemux', '!', 'mpegaudioparse', '!',
                'filesink', 'location={}'.format(aac_name)]

        p=subprocess.Popen(cmd)
        p.wait()
        retcode=p.returncode

        return retcode


    def mk_audio_png(self, src, png_name):
        """
        make audio png from source,
        src can be http:// or file://
        dst is the local fs.
        """
        p = gslevels.Make_png()
        # p = gslevels.Make_mlt_fix_1()
        p.location = src
        p.verbose = self.options.verbose
        p.setup()
        p.start()
        ret = p.mk_png(png_name)

        return ret

    def mk_low(self, rfpathname, out):


        # symaphore? so a 2nd process doesn't do this file too
        # cmd = ['touch', out]
        # self.run_cmd(cmd)

        # tmp = f"{out}.tmp"

        # vb = "100k"
        # ab = "75k"
        vb, ab = "200k", "256k"

        cmd = [
                'gst-launch-1.0', '-e',
                'filesrc', 'location=13_05_53.ts', '!',
                'decodebin', 'name=decode', '!',
                'x264enc', '!',
                'queue', '!',
                'mp4mux', 'name=mp4mux', '!',
                'filesink', 'location=', '13_05_53.ts.x.mp4',
                'decode.', '!',
                'audioconvert', '!',
                'lamemp3enc', 'bitrate=128', '!',
                'queue', '!',
                'mp4mux.']

        cmd = ["melt", rfpathname,
                "meta.attr.titles=1",
                "meta.attr.titles.markup=#timecode#",
                "-attach", "data_show", "dynamic=1",
                "-consumer", "avformat:"+out,
                "progress=1",
                "vcodec=libx264", "vb="+vb,
                "acodec=aac", "ab="+ab,
                "strict=-2",
                "preset=ultrafast",
                "movflags=+faststart", ]
        # , "threads=6"]
                # "properties=x264-medium",
        """
        xcmd = ["ffmpeg", "-i", rfpathname,
            "-vf", "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf: text='%{pts\:hms}': fontcolor=black@0.8: fontsize=48: x=7: y=500",
            "-codec:v", "libx264", "-b:v", vb,
            "-codec:a", "aac", "-strict", "-2", "-b:a", ab,
            "-preset", "ultrafast", "-f", "mp4", "-y", out]
        """

        p=subprocess.Popen(cmd)
        p.wait()
        retcode=p.returncode

        # cmd = ['mv', tmp, out]
        # self.run_cmd(cmd)

    def rf_web(self, show, rf):
        """
        make a low bitrate version of the raw file
        for previewing over the web
        """

        for ext in self.options.upload_formats:

            base = os.path.join("dv", rf.location.slug, rf.filename)
            web_base = os.path.join("web", "raw",
                    rf.location.slug, rf.filename)
            rfpathname = os.path.join(self.show_dir, base)
            low = f"{web_base}.{ext}"
            if self.options.verbose:
                print(f'{base} -> {low}')
            out = os.path.join(self.show_dir, low)

            os.makedirs(os.path.dirname(out), exist_ok=True)

            # look for low on local file system
            # or --replace
            # or the source is newer
            if (not os.path.exists(out) or
                self.options.replace or
                (os.stat(rfpathname).st_mtime > os.stat(out).st_mtime)):

                self.mk_low(rfpathname, out)

            if self.options.rsync:
                # if not self.cdn_exists(show, low) or self.options.replace:
                self.file2cdn(show, low, mkdir=self.options.mkdir)
                    # raw file (huge!!! over 5 gig each)
                    ### self.file2cdn(show, base)


    def rf_audio(self, show, rf):

        rf_tail = os.path.join( "dv", rf.location.slug, rf.filename )
        aac_tail = "{rf_tail}.aac".format(rf_tail=rf_tail)

        src = os.path.join(self.show_dir,rf_tail)
        dst = os.path.join(self.show_dir,aac_tail)

        if (not os.path.exists(dst) or
                self.options.replace or
                (os.stat(src).st_mtime > os.stat(dst).st_mtime)):
            ret = self.mk_audio(src,dst)

        if self.options.rsync and (
                not self.cdn_exists(show,aac_tail) or self.options.replace):
            print("uploading audio: {}".format(aac_tail))
            self.file2cdn(show,aac_tail)


    def rf_audio_png(self, show, rf):

        rf_tail = os.path.join("dv", rf.location.slug, rf.filename)
        png_tail = os.path.join("web", "raw",
                rf.location.slug, rf.filename + ".wav.png")

        src = os.path.join(self.show_dir, rf_tail)
        dst = os.path.join(self.show_dir, png_tail)

        if not os.path.exists(dst) or self.options.replace:
            ret = self.mk_audio_png(src,dst)

        if self.options.rsync and (
                not self.cdn_exists(show,png_tail) or self.options.replace):
            self.file2cdn(show,png_tail)


    def raw_file(self, show, rf):

        base = os.path.join( "dv", rf.location.slug, rf.filename )
        if self.options.verbose: print("rf: {}".format(base))
        src_name = os.path.join(self.show_dir, base)

        if not os.path.exists(src_name):
            print("src not found: {src_name}".format(
                src_name=src_name))
            if self.options.delete_unknown:
                rf.delete()
                return
            raise IOError

        if self.options.low:
            self.rf_web(show, rf)
        if self.options.audio:
            self.rf_audio(show, rf)
        if self.options.audio_viz:
            self.rf_audio_png(show, rf)


    def raw_files(self, show):

        if self.options.verbose: print("getting raw files...")

        rfs = Raw_File.objects.filter(show=show,)

        if self.options.day:
            rfs = rfs.filter(start__day=self.options.day)

        if self.options.room:
            loc = Location.objects.get(slug=self.options.room)
            rfs = rfs.filter(location = loc)

        if self.options.include:
            rfs = rfs.filter(filename=self.options.include)

        # rfs = rfs.exclude(id=12212)
        # rfs = rfs.exclude(filesize__lt=800000)
        # rfs = rfs.exclude(filename="2016-07-30/12_55_51.ts")

        if self.options.ready_state is not None or self.args:
            # if both are passed, just do the list of eps.
            if self.args:
                eps = Episode.objects.filter(id__in=self.args)
            else:
                eps = Episode.objects.filter(state=self.ready_state)
            cls = Cut_List.objects.filter(episode__in=eps)
            rfs = rfs.filter(cut_list__in=cls).distinct()

        """
        # try to do the more important ones first
        # rfs = rfs.order_by()
        # ok can't figure out good SQL stuff, so ... hammer time.
        # skip before 8am and after 6pm
        # it would be nice to target ones that are being worked on
        # but that's too hard.

        for rf in rfs:

            if rf.start.hour < 8:
                # too early, must be tests
                continue
            if rf.start.hour > 18:
                # too late, mixer was left on after talks stopped
                # or it is an evening event, oh well too bad.
                continue

            self.raw_file(show,rf)
        """

        # now do them all of them to be sure.
        # does't cost much to check and see they are done.
        for rf in rfs:
            self.raw_file(show, rf)

    def sync_final(self,show,ep):
        for ext in self.options.upload_formats:
            base = os.path.join( ext, "{}.{}".format(ep.slug, ext) )
            if not self.cdn_exists(show,base) or self.options.replace:
                self.file2cdn(show,base)

    def sync_final_audio_png(self,show,ep):

        for ext in self.options.upload_formats:

            src_tail = os.path.join(ext, ep.slug + ".{}".format(ext) )
            png_tail = os.path.join("web", "cooked",
                    "{src_tail}.wav.png".format(src_tail=src_tail))

            src_name = os.path.join(self.show_dir, src_tail)
            png_name = os.path.join(self.show_dir, png_tail)

            if os.path.exists(src_name):

                if not os.path.exists(png_name) or self.options.replace:
                    # self.mk_audio_png(ep.public_url, png_name)
                    self.mk_audio_png(src_name, png_name)

                if self.options.rsync:
                    self.file2cdn(show, png_tail)

            else:

                if self.options.verbose:
                    print("src not found: {src_name}".format(
                        src_name=src_name))


    def cut_list(self,show,ep):
        if self.options.verbose: print("#{} cut list".format(ep.id))
        cls = ep.cut_list_set.all()
        for cl in cls:
            if self.options.verbose: print("raw: {}".format(cl.raw_file))
            self.rf_web(show, cl.raw_file)


    def sync_title_png(self,show,ep):
        base = os.path.join("titles", ep.slug )
        # if self.options.replace:
        #    print(f"{base=}")
        self.file2cdn(show, f"{base}.svg")
        self.file2cdn(show, f"{base}.png")


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
        # import code; code.interact(local=locals())
        eps = Episode.objects.filter(show=show)

        if self.options.day:
            eps = eps.filter(start__day=self.options.day)

        if self.options.room:
            loc = Location.objects.get(slug=self.options.room)
            eps = eps.filter(location = loc)

        if self.args:
            eps = eps.filter(id__in=self.args)

        # eps = eps.filter(state=8)

        for ep in eps:
            print(ep)

            # if self.options.assets and self.options.rsync:
            if self.options.rsync:
                self.sync_title_png(show, ep)
                self.mlt(show,ep)

            if self.options.rsync:
                # self.sync_final(show, ep)
                pass

            if self.options.audio_viz:
                self.sync_final_audio_png(show,ep)

            if self.options.raw:
                self.cut_list(show,ep)

            # if ep.state>1:
            #    return


    def show_assets(self,show):

        loc_dir=os.path.join(self.show_dir, 'assets')

        if True:
            # create title png file
            svg_name = os.path.join(
                    loc_dir,"titles", show.client.title_svg)
            png_name = svg_name + ".png"
            if os.path.exists(png_name):
                os.remove(png_name)
            cmd = ["inkscape", svg_name,
               "--export-filename", png_name,
               "--export-type", "png",
                   ]
            ret = self.run_cmd(cmd)
            ret = os.path.exists(png_name)
            if not ret:
                print("error?!")
                return

        # walk the assets dir looking for random files ;/
        if self.options.rsync:

            for dirpath, dirnames, filenames in os.walk(loc_dir,followlinks=True):
                stuby=dirpath[len(self.show_dir)+1:]
                if self.options.verbose: print(f"{stuby=}")

                for dirname in dirnames:
                    self.dir2cdn(show,dirname)

                for filename in filenames:
                    base = os.path.join(stuby,filename)
                    if self.options.verbose: print(f"{base=}")
                    self.file2cdn(show,base)


    def init_rax(self, show):

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

        # if self.options.rsync:
        #    self.init_rax(show)

        if self.options.assets:
            print("doing one_show ... self.show_assets...")
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
           help="sync asset files (mlt, svg, png (not raw or lq raw)).")
        parser.add_option('--raw', action="store_true",
           help="process raw files.")
        parser.add_option('--low', action="store_true",
           help="make low quality files.")
        parser.add_option('--audio', action="store_true",
           help="make audio only files.")
        parser.add_option('--audio-viz', action="store_true",
           help="make audio visualization files.")
        parser.add_option('--cooked', action="store_true",
           help="process cooked files.")
        parser.add_option('--rsync', action="store_true",
            help="upload to DS box.")
        parser.add_option('--mkdir', action="store_true",
            help="mkdir destination dirs on remote box")
        parser.add_option('--delete-unknown', action='store_true',
            help="Delete any file records from the database, if we can't "
                 "find them on disk.")

        parser.add_option('--include',
                help="only include this filename. (What is stored in raw_file.filnema: yyyy-mm-dd/hh_mm_ss.ts)")

        parser.add_option('--replace', action="store_true",
            help="Upload again, step on existing file.")


if __name__=='__main__':
    p=SyncRax()
    p.main()


