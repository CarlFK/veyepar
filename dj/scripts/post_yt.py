#!/usr/bin/python

# posts to youtube

import youtube_v3_uploader
import archive_uploader
import rax_uploader

import os
import pprint

import pw

from process import process
from django.db import DatabaseError
from django.template.defaultfilters import slugify

from add_to_richard import get_video_id

from main.models import Show, Location, Episode, Raw_File, Cut_List

class FileNotFound(Exception):
    def __init__(self, value):
        self.value=value
    def __str__(self):
        return repr(self.value)

class post(process):

    ready_state = 4

    def construct_description(self, ep):
        # collect strings from various sources
        # build a wad of text to use as public facing description 

        show = ep.show
        client = show.client

        descriptions = [ep.authors,
                ep.public_url, ep.conf_url,
                ep.description,
                ]
                # show.description, client.description]

        # remove blanks
        descriptions = [d for d in descriptions if d]
        # combine wiht CRs between each item
        description = "\n".join(descriptions)
        # description = "<br/>\n".join(description.split('\n'))

        return description 

    def get_tags(self,ep):

        tags = [ ep.show.client.slug, ep.show.slug, ] 

        for more_tags in [ ep.show.client.tags, ep.tags, ep.authors ]:
            if more_tags is not None:
                tags += more_tags.split(',')

        # remove spaces
        tags = [ tag.replace(' ','') for tag in tags ]

        # remove any empty tags
        tags = filter(None, tags)

        return tags

    def get_files(self, ep):
        # get a list of video files to upload
        # blip and archive support multiple formats, youtube does not.
        # youtube and such will only upload the first file.
        files = []
        for ext in self.options.upload_formats:
            src_pathname = os.path.join( self.show_dir, ext, "%s.%s"%(ep.slug,ext))
            if os.path.exists(src_pathname):
                files.append({'ext':ext,'pathname':src_pathname})
            else:
                # crapy place to abort, but meh, works for now.
                # maybe this is the place to use raise?
                print "not found:", src_pathname

                raise FileNotFound(src_pathname)

        if self.options.debug_log:

            # put the mlt and .sh stuff into the log
            # blip and firefox want it to be xml, so jump though some hoops
            log = "<log>\n"
            mlt_pathname = os.path.join( self.show_dir, 'tmp', "%s.mlt"%(ep.slug,))
            log += open(mlt_pathname).read()
            sh_pathname = os.path.join( self.show_dir, 'tmp', "%s.sh"%(ep.slug,))
            shs = open(sh_pathname).read().split('\n')
            shs = [ "<line>\n%s\n</line>\n" % l for l in shs if l]
            log += "<shell_script>\n%s</shell_script>\n" % ''.join(shs)
            log += "</log>"

            # blip says: try something like a tt or srt file
            log_pathname = os.path.join( self.show_dir, 'tmp', "%s.tt"%(ep.slug,))
            log_file=open(log_pathname,'w').write(log)
            # add the log to the list of files to be posted
            files.append({'ext':'tt', 'pathname':log_pathname})

        return files

    def collect_metadata(self, ep):

        meta = {}
        meta['title'] = ep.name
        meta['description'] = self.construct_description(ep)
        meta['tags'] = self.get_tags(ep)

        # if ep.license:
        #    meta['license'] = str(ep.license)

        # meta['rating'] = self.options.rating

        # http://gdata.youtube.com/schemas/2007/categories.cat
        meta['category'] = 22 # "Education"

        if ep.location.lat and ep.location.lon:
            meta['latlon'] = (ep.location.lat, ep.location.lon)

        meta['privacyStatus'] = 'unlisted'

        return meta

    def mk_key(self, ep, f):
        # make a key for rackspace cdn object key value store 
        #  <category-slug>/<video-id>_<title-of-video>.mp4
        # if we have that data handy.
        key = ''
        if ep.show.client.category_key:
            # warning: this does not take into account pvo collisions
            # https://github.com/willkg/richard/blob/master/richard/videos/utils.py#L20  def generate_unique_slug(obj, slug_from, slug_field='slug'):
            key += slugify( ep.show.client.category_key ) + '/'

        if ep.public_url:
            key += get_video_id( ep.public_url) + "_"

        key += ep.slug[:50] + "." + f['ext']

        return key

    def do_yt(self,ep,files,private,meta):

        youtube_success = False

        uploader = youtube_v3_uploader.Uploader()

        uploader.user = ep.show.client.youtube_id
        uploader.files = files
        uploader.meta = meta
        uploader.private = private

        # for replacing.
        # (currently not implemented in youtube_v3_uploader
        uploader.old_url = ep.host_url

        if self.options.test:
            print 'test mode:'
            print "user key:", uploader.user
            print 'files = %s' % files
            print 'meta = %s' % pprint.pformat(meta)
            print 'skipping youtube_upoad.py uploader.upload()'
            print len(meta['description'])

        # elif ep.host_url:
        #    print "skipping youtube, already there."
        #    youtube_success = True

        else:

            # down to next layer of code that will do the uploading
            # uploader.debug_mode=True
            youtube_success = uploader.upload()


            if youtube_success:
                if self.options.verbose: print uploader.new_url

                # save new youtube url
                ep.host_url = uploader.new_url
                # for test framework
                self.last_url = uploader.new_url

            else:
                print "youtube error! zomg"
                ep.comment += "\n%s\n" % (uploader.ret_text.decode('utf-8').encode('ascii', 'xmlcharrefreplace'))

        return youtube_success

    def do_arc(self, ep, files, meta):
        # upload to archive.org too.. yuck.
        # this should be in post_arc.py, but
        # but I don't want 2 processes uploading at the same time.
        # bcause bandwidth?

        uploader = archive_uploader.Uploader()

        uploader.user = ep.show.client.archive_id
        uploader.bucket_id = ep.show.client.bucket_id

        for f in files:

            uploader.pathname = f['pathname']
            uploader.key_id = "%s.%s" % ( ep.slug[:30], f['ext'] )

            if self.options.test:
                print 'test mode...'
                print 'skipping archive_uploader .upload()'

            # elif ep.archive_mp4_url:
            #    print "skipping archive, already there."
            #    archive_success = True

            else:

                # actually upload
                # uploader.debug_mode=True
                archive_success = uploader.upload()
                if archive_success:
                    if self.options.verbose: print uploader.new_url
                    # this is pretty gross.
                    # store the archive url
                    if f['ext'] == "mp4":
                        ep.archive_mp4_url = uploader.new_url
                    elif f['ext'] == "ogv":
                        ep.archive_ogv_url = uploader.new_url
                    elif f['ext'] == "webm": # omg super gross.
                        ep.archive_ogv_url = uploader.new_url

                    # hook for tests so that it can be browsed
                    self.archive_url = uploader.new_url
                    # for test framework
                    self.last_url = uploader.new_url


                else:
                    print "internet archive error!"

            return archive_success


    def do_rax(self, ep, files, meta):
        # upload to archive.org too.. yuck.
        # this should be in post_arc.py, but
        # but I don't want 2 processes uploading at the same time.
        # bcause bandwidth?

        success = False

        uploader = rax_uploader.Uploader()

        uploader.user = ep.show.client.rax_id
        uploader.bucket_id = ep.show.client.bucket_id

        for f in files:

            uploader.pathname = f['pathname']
            uploader.key_id = self.mk_key(ep, f)

            if self.options.test:
                print 'test mode...'
                print 'skipping rax_uploader .upload()'
                print 'key_id:', uploader.key_id

            # elif ep.rax_mp4_url:
            #    print "skipping archive, already there."
            #    rax_success = True

                success = True

            else:

                # actually upload
                # uploader.debug_mode=True
                success = uploader.upload()
                
                # possible errors:
                # invalid container - halt, it will likely be invalid for all 
                # transmission - retry
                # bad name, mark as error and continue to next

                if success:
                    if self.options.verbose: print uploader.new_url
                    # this is pretty gross.
                    # store the url
                    if f['ext'] == "mp4":
                        ep.rax_mp4_url = uploader.new_url
                    elif f['ext'] == "ogv":
                        ep.rax_ogv_url = uploader.new_url

                    # hook for tests so that it can be browsed
                    # self.rax_url = uploader.new_url
                    # for test framework
                    self.last_url = uploader.new_url


                else:
                    print "rax error!"

            return success

    def process_ep(self, ep):

        if not ep.released: # and not self.options.release_all:
            # --release will force the upload, overrides ep.released
            if self.options.verbose: print "not released:", ep.released
            return False

        # collect data needed for uploading
        files = self.get_files(ep)
        if self.options.verbose: 
            print "[files]:",
            pprint.pprint(files)

        meta = self.collect_metadata(ep)
        if self.options.verbose: pprint.pprint(meta)

        # upload
        if not ep.show.client.youtube_id: youtube_success = True
        else: youtube_success = self.do_yt(ep,files,True,meta)

        # if not ep.show.client.archive_id: archive_success = True
        # else: archive_success = self.do_arc(ep,files,meta)

        if not ep.show.client.rax_id: rax_success = True
        else: rax_success = self.do_rax(ep,files,meta)

        # tring to fix the db timeout problem
        try:
            ep.save()
        except DatabaseError, e:
            from django.db import connection
            connection.connection.close()
            connection.connection = None
            ep.save()

        return True
                # youtube_success 
                # and archive_success \
                # and rax_success

    def add_more_options(self, parser):

        parser.add_option('--release-all', action="store_true",
            help="ignore the released setting.")

if __name__ == '__main__':
    p=post()
    p.main()
