#!/usr/bin/python

# posts to youtube (and other hosting services)

from process import process

import youtube_v3_uploader
import ia_uploader
# import rax_uploader

import os
from pprint import pprint
import re

import pw

from django.template.defaultfilters import slugify

# from add_to_richard import get_video_id

from django.conf import settings
from main.models import Show, Location, Episode, Raw_File, Cut_List

class FileNotFound(Exception):
    def __init__(self, value):
        self.value=value
    def __str__(self):
        return repr(self.value)

class post(process):

    ready_state = 4

    def get_tags(self,ep):

        tags = [ ep.show.client.slug, ep.show.slug, ]

        # for more_tags in [ ep.show.client.tags, ep.tags, ep.authors ]:
        for more_tags in [ ep.show.client.tags, ep.authors ]:
            if more_tags is not None:
                tags += more_tags.split(',')

        # remove spaces
        tags = [ tag.replace(' ','') for tag in tags ]

        # remove any empty tags
        tags = [_f for _f in tags if _f]

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
                print("not found:", src_pathname)

                raise FileNotFound(src_pathname)

        if self.options.debug_log:

            # put the mlt and .sh stuff into the log
            # blip and firefox want it to be xml, so jump though some hoops
            log = "<log>\n"
            mlt_pathname = os.path.join( self.show_dir, 'mlt', "%s.mlt"%(ep.slug,))
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
        meta['title'] = '"{title}" - {authors} ({show})'.format(
                title=ep.name, authors=ep.authors, show=ep.show.name)

        if len(meta['title']) > 100:
            meta['title'] = ep.name

        meta['authors'] = ep.authors.split(',')
        meta['description'] = ep.composed_description()
        meta['tags'] = self.get_tags(ep)

        meta['start'] = ep.start
        meta['language'] = ep.language
        meta['language'] = "eng"

        # YouTube treats 'creativeCommon' == 'CC BY 3.0'
        # Only use it when the license **exactly** matches that, even if for
        # a different CC license.
        # Reference: https://support.google.com/youtube/answer/2797468?hl=en
        # Context: https://2019.pycon-au.org/news/video-licencing-changes/
        if ep.license and (ep.license.upper().replace('-', ' ') in (
                'CC BY', 'CC BY 3.0')):
            meta['license'] = 'creativeCommon'
        else:
            # We're not sure -- play it safe.
            meta['license'] = 'youtube'

        # meta['rating'] = self.options.rating

        # http://gdata.youtube.com/schemas/2007/categories.cat
        meta['categoryId'] = 27 # "Education"

        if ep.location.lat and ep.location.lon:
            meta['latlon'] = (ep.location.lat, ep.location.lon)

        meta['privacyStatus'] = 'unlisted'

        return meta

    def mk_key(self, ep, f):
        # make a key for rackspace cdn object key value store
        #  <category-slug>/<video-id>_<title-of-video>.mp4
        # if we have that data handy.
        # otherwise client/show/slug
        key = ''

        if ep.show.client.category_key:
            # warning: this does not take into account pvo collisions
            # https://github.com/willkg/richard/blob/master/richard/videos/utils.py#L20  def generate_unique_slug(obj, slug_from, slug_field='slug'):
            key += slugify( ep.show.client.category_key ) + '/'
        else:
            key += ep.show.client.slug + '/'+ ep.show.client.slug + '/'


        if ep.public_url:
            key += get_video_id( ep.public_url) + "_"

        key += ep.slug[:50] + "." + f['ext']

        return key

    def do_yt(self, ep,files, private, meta):

        youtube_success = False

        # https://developers.google.com/youtube/v3/docs/videos#resource
        assert len(meta['title'])<=100, "len(name) > maximum length of 100"

        uploader = youtube_v3_uploader.Uploader()

        uploader.token_file = settings.SECRETS_DIR / "youtube" / pw.yt[ep.show.client.youtube_id]['filename']
        uploader.client_secrets_file = settings.GOOG_CLIENT_SECRET

        uploader.pathname = files[0]['pathname']
        uploader.meta = meta
        uploader.private = private

        if self.options.test:
            print('test mode:')
            print(f"{uploader.token_file=}")
            print(f"{uploader.client_secrets_file=}")
            print('files = %s' % files)
            print('meta = %s' % pprint.pformat(meta))
            print('skipping youtube_upoad.py uploader.upload()')
            print(len(meta['description']))

        elif self.options.update_description:
            # I don't like where this code lives. (currently here.)

            # required to update (I don't know why...)
            title = meta['title']
            categoryId = meta['categoryId']

            description=meta['description']

            if self.options.verbose:
                print(description)

            uploader.set_description(ep.host_url, description=description, title=title, categoryId=categoryId)

            self.sate = None
            return False

        elif ep.host_url and not self.options.replace:
            print("skipping youtube, already there.")
            youtube_success = True

        else:

            if ep.host_url:
                uploader.delete_video(ep.host_url)

            # down to next layer of code that will do the uploading
            # uploader.debug_mode=True
            youtube_success = uploader.upload()

            if youtube_success:
                # if self.options.verbose: print uploader.new_url
                print((uploader.new_url))

                # save new youtube url
                ep.host_url = uploader.new_url
                # the thumb url
                ep.thumbnail = uploader.thumbnail

                # for test framework
                self.last_url = uploader.new_url

            else:
                print("youtube error! zomg")
                ep.comment += "\n%s\n" % (uploader.ret_text.decode('utf-8').encode('ascii', 'xmlcharrefreplace'))

            self.save_me(ep)

        return youtube_success

    def do_ia(self, ep, files, meta):

        # upload to archive.org too.
        # this should be in post_ia.py, but
        # but I don't want 2 processes uploading at the same time.
        # bcause bandwidth?

        uploader = ia_uploader.Uploader()

        uploader.user = ep.show.client.archive_id

        # transform veyepar meta to ia meta

        if ep.license.upper().startswith('CC'):
            x=ep.license[3:8].lower()
            ver='4.0'
            meta['licenseurl'] = f'http://creativecommons.org/licenses/{x}/{ver}/'

        for f in files:

            uploader.pathname = f['pathname']
            uploader.verbose = self.options.verbose

            slug = "{show}-{slug}".format(
                    show=ep.show.slug,
                    slug=ep.slug)[:100]

            # IA requires this: ^[a-zA-Z0-9][a-zA-Z0-9_.-]{4,100}$
            slug = re.sub(r'[^a-zA-Z0-9_.-]', '', slug)

            uploader.slug = slug

            uploader.meta = meta

            if self.options.test:
                print('test mode...')
                print('skipping archive_uploader .upload()')
                ia_success = False

            elif ep.archive_url and not self.options.replace:
                print("skipping archive, file already there.")
                ia_success = True

            else:
                # actually upload
                # uploader.debug_mode=True
                ia_success = uploader.upload()
                if ia_success:
                    if self.options.verbose: print(uploader.new_url)
                    # store the archive url (page)
                    ep.archive_url = uploader.new_url

                    archive_file_url = "{page}/{slug}.{ext}".format(
                            page=uploader.new_url,
                            slug=ep.slug,
                            ext=f['ext'])

                    # this is pretty gross.
                    if f['ext'] == "mp4":
                        ep.archive_mp4_url = archive_file_url
                    elif f['ext'] == "ogv":
                        ep.archive_ogv_url = archive_file_url
                    elif f['ext'] == "webm": # omg super gross.
                        ep.archive_ogv_url = archive_file_url

                    # hook for tests so that it can be browsed
                    self.archive_url = uploader.new_url
                    # for test framework
                    self.last_url = uploader.new_url

                else:
                    print("Internet archive.org error!")

                self.save_me(ep)

            return ia_success


    def do_rax(self, ep, files, meta):
        # upload to rackspace cdn too.. yuck.
        # this should be in post_rax.py, but
        # but I don't want 2 processes uploading at the same time.
        # bcause bandwidth?  or something.
        # Not sure what the problem is really.

        if self.options.verbose: print("do_rax...")

        success = False

        uploader = rax_uploader.Uploader()

        uploader.user = ep.show.client.rax_id
        uploader.bucket_id = ep.show.client.bucket_id

        for f in files:

            uploader.pathname = f['pathname']
            uploader.key_id = self.mk_key(ep, f)

            if self.options.test:
                print('test mode...')
                print('skipping rax_uploader .upload()')
                print('key_id:', uploader.key_id)

            elif ep.rax_mp4_url and not self.options.replace:
                # above assumes rax_mp4_url is what gets filled in below
                # this is so gross.
                print("skipping rax, already there.")
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
                    if self.options.verbose: print(uploader.new_url)
                    # this is pretty gross.
                    # store the url
                    if f['ext'] == "mp4":
                        ep.rax_mp4_url = uploader.new_url
                    elif f['ext'] == "webm":
                        ep.rax_mp4_url = uploader.new_url
                    elif f['ext'] == "ogv":
                        # there is no ep.rax_ogv_url
                        ep.rax_ogv_url = uploader.new_url

                    # hook for tests so that it can be browsed
                    # self.rax_url = uploader.new_url
                    # for test framework
                    self.last_url = uploader.new_url


                else:
                    print("rax error!")

                self.save_me(ep)

            return success

    def do_vimeo(self,ep,files,private,meta):

        vimeo_success = False

        uploader = vimeo_uploader.Uploader()

        uploader.user = ep.show.client.vimeo_id
        uploader.pathname = files[0]['pathname']
        uploader.meta = meta

        if self.options.test:
            print('test mode:')
            print("user key:", uploader.user)
            print('files = %s' % files)
            print('meta = %s' % pprint.pformat(meta))
            print('skipping vimeo_upoad.py uploader.upload()')
            print(len(meta['description']))

        elif ep.host_url and not self.options.replace:
            print("skipping vimeo, already there.")
            youtube_success = True

        else:

            # down to next layer of code that will do the uploading
            # uploader.debug_mode=True
            youtube_success = uploader.upload()


            if youtube_success:
                if self.options.verbose: print(uploader.new_url)

                # save new youtube url
                ep.host_url = uploader.new_url
                # for test framework
                self.last_url = uploader.new_url

            else:
                print("youtube error! zomg")
                ep.comment += "\n%s\n" % (uploader.ret_text.decode('utf-8').encode('ascii', 'xmlcharrefreplace'))

            self.save_me(ep)

        return youtube_success

    def process_ep(self, ep):

        if not ep.released and ep.released is not None: # and not self.options.release_all:
            # --release will force the upload, overrides ep.released
            if self.options.verbose: print("not released:", ep.released)
            return False

        # collect data needed for uploading
        files = self.get_files(ep)
        if self.options.verbose:
            print("[files]:", end=' ')
            pprint(files)

        meta = self.collect_metadata(ep)
        if self.options.verbose: pprint(meta)

        # process youtube
        if not ep.show.client.youtube_id: youtube_success = True
        else: youtube_success = self.do_yt(ep,files,True,meta)

        # process archive.org
        if not ep.show.client.archive_id: archive_success = True
        else: archive_success = self.do_ia(ep,files,meta)

        # process rackspace cdn
        # needs a rackspace account
        # if not ep.show.client.rax_id: rax_success = True
        # else: rax_success = self.do_rax(ep,files,meta)

        # process vimeo (needs upgrading to new api)
        # if not ep.show.client.vimeo_id: vimeo_success = True
        # else: vimeo_success = self.do_vimeo(ep,files,meta)

        return True
                # youtube_success
                # and archive_success \
                # and rax_success

    def add_more_options(self, parser):

        parser.add_option('--replace', action="store_true",
            help="Upload again, step on existing URL.")

        parser.add_option('--release-all', action="store_true",
            help="ignore the released setting (assuming this is enabled.)")

        parser.add_option('--update-description', action="store_true",
            help="Just update description of existing upload.")




if __name__ == '__main__':
    p=post()
    p.main()
