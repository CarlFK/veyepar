#!/usr/bin/python

# posts to a local dir
# for fosdem, 
# (02:50:17 PM) h01ger: please use $room/$day/$talk
# (02:51:41 PM) h01ger: i think "saturday" is beter

# Maybe this should be a config stored in the client?
# It is the first time in 5 years it has come up, so 
# for now, just hack this code.

import os
import shutil
import pprint

from process import process

from main.models import Show, Location, Episode, Raw_File, Cut_List

class FileNotFound(Exception):
    def __init__(self, value):
        self.value=value
    def __str__(self):
        return repr(self.value)

class post(process):

    ready_state = 11

    def get_files(self, ep):
        # get a list of video files to upload
        # blip and archive support multiple formats, youtube does not.
        # youtube and such will only upload the first file.
        files = []
        for ext in self.options.upload_formats:
            src_pathname = os.path.join( self.show_dir, ext, "%s.%s"%(ep.slug,ext))
            if self.options.verbose: print src_pathname

            if os.path.exists(src_pathname):
                files.append({'ext':ext,'pathname':src_pathname})
            else:
                # crapy place to abort, but meh, works for now.
                # maybe this is the place to use raise?
                print "not found:", src_pathname

                raise FileNotFound(src_pathname)

        return files

    def process_ep(self, ep):

        # host_url = "http://video.fosdem.org"
        host_url = "http://mirror.linux.org.au/linux.conf.au"
        local_dir = "to-mirror"

        if not ep.released and not self.options.release_all:
            # --release-all will force the upload, overrides ep.released
            if self.options.verbose: print "not released:", ep.released
            return False

        # collect data needed for uploading
        files = self.get_files(ep)
        if self.options.verbose: 
            print "[files]:",
            pprint.pprint(files)


        for fn in files:
            # construct a dest dir of the form year/room/Day 
            dest = os.path.join( 
                ep.start.strftime("%Y"), 
                ep.location.slug, 
                ep.start.strftime("%A"),
                )

            # this is the dir the website will want
            # add the filename to be nice
            ep.public_url = "/".join([ 
                    host_url,
                    dest, "%s.%s"%(ep.slug,fn['ext'])])
            if self.options.verbose: print "public", ep.public_url

            # add the local fs dir home:
            dest = os.path.join( self.show_dir, local_dir, dest )

            # make sure the dir exists
            if self.options.verbose: print "dest", dest
            if not os.path.exists(dest): os.makedirs(dest)

            if self.options.test:
                # check for existance of source and dest
                print("src: {} {}".format(
                    fn['pathname']),
                    "found." if os.path.exists(fn['pathname']) else "not found."
                )
                filename = os.path.split(fn['pathname'])[1]
                dest = os.path.join(dest,filename)
                
                print("dst: {} {}".format(
                    dest),
                    "found." if os.path.exists(fn['pathname']) else "not found."
                )
            else:

                # copy the file
                shutil.copy( fn['pathname'], dest )


        ep.save()

        return True

    def add_more_options(self, parser):
        parser.add_option('--release-all', action="store_true",
            help="override the released setting.")

if __name__ == '__main__':
    p=post()
    p.main()
