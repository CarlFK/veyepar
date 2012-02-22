#!/usr/bin/python

# posts to youtube

import youtube_uploader

import os

import pw
from process import process

from main.models import Show, Location, Episode, Raw_File, Cut_List

class post(process):

  ready_state = 4

  def process_ep(self, ep):
    if self.options.verbose: print ep.id, ep.name
    if not ep.released and not self.options.release_all:
        # --release will force the upload, overrides ep.released
        if self.options.verbose: print "not released:", ep.released
        return False

    loc = ep.location
    show = ep.show
    client = show.client

    descriptions = [ep.authors, ep.description, show.description, client.description]
    descriptions = [d for d in descriptions if d]
    description = "\n".join(descriptions)
    # description = "<br/>\n".join(description.split('\n'))

    meta = {
        'title': ep.name,
        'description': description[:250],
        }

    tags = [ self.options.topics, client.slug, client.tags, show.slug, ep.tags ]
    authors = ep.authors.split(',')
    authors = [ a.replace(' ','') for a in authors ]
    tags += authors 

    meta['tags'] = [tag for tag in tags if tag] 

    if ep.license: 
        meta['license'] = str(ep.license)
    elif self.options.license:
        meta['license'] = self.options.license

    if self.options.rating:
        meta['rating'] = self.options.rating

    if self.options.category:
        meta['category'] = self.options.category
        # http://gdata.youtube.com/schemas/2007/categories.cat
        # meta['category'] = "Education"

    if self.options.hidden:
        meta['hidden'] = self.options.hidden

    if ep.location.lat and ep.location.lon:
        meta['latlon'] = (ep.location.lat, ep.location.lon)


    # private is implemnted different in youtube and blip.
    # plit want's a number, yt wants Truthy
    meta['hidden'] = ep.hidden or self.options.hidden

    # find a thumbnail
    # check for episode.tumb used in the following:
    # 1. absololute path (dumb?)
    # 2. in tumb dir (smart)
    # 3. relitive to show dir (not completely wonky)
    # 4. in tumb dir, same name as episode.png (smart)
    # if none of those, then grab the thumb from the first cut list file
    found=False
    for thumb in [ 
          ep.thumbnail,
          os.path.join(self.show_dir,'thumb',ep.thumbnail),
          os.path.join(self.show_dir,ep.thumbnail),
          os.path.join(self.show_dir,'thumb',ep.slug+".png"),]:
          if os.path.isfile(thumb): 
              found=True
              break
    if not found:
         for cut in Cut_List.objects.filter(
                 episode=ep,apply=True).order_by('sequence'):
             basename = cut.raw_file.basename()        
             thumb=os.path.join(self.episode_dir, "%s.png"%(basename))
             if os.path.exists(thumb): 
                 found=True
                 break
    if not found: thumb=''

    # get a list of video files to upload
    # blip supports multiple formats, youtube does not.
    # youtube and such will only upload the first file.
    files = []
    for ext in self.options.upload_formats:
        src_pathname = os.path.join( self.show_dir, ext, "%s.%s"%(ep.slug,ext))
        files.append({'ext':ext,'pathname':src_pathname})

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

        
    # look for username in [options, client, first in pw.py]
    # password always comes from pw.py
   
    host_user =  self.options.host_user if self.options.host_user \
                    else client.host_user if client.host_user \
                    else pw.host.keys()[0]

    if self.options.test:
        print 'test mode:'
        print 'files %s' % files
        print 'meta %s' % meta
        print 'thumb %s' % thumb
        print

    else:
   
        uploader = youtube_uploader.Uploader()

        uploader.files = files
        uploader.thumb = thumb
        uploader.meta = meta
        uploader.user = host_user

        uploader.old_url = ep.host_url # for replacing.
     
        ret = uploader.upload()

        ep.comment += "\n%s\n" % (uploader.ret_text.decode('utf-8').encode('ascii', 'xmlcharrefreplace'))

        # self.log_info(uploader.ret_text)

        if ret:

            if self.options.verbose: print uploader.new_url
            ep.host_url = uploader.new_url
            self.last_url = uploader.new_url # hook for tests so that it can be browsed

            print dir(uploader)
            import code
            # code.interact(local=locals())

        else:
            print "error!"

        ep.save()

        return ret

  def add_more_options(self, parser):
        parser.add_option('--host-user', 
            help='video host account name (pass stored in pw.py)')
        parser.add_option('--rating', 
            help="TV rating")
        parser.add_option('-T', '--topics',
            help="list of topics (user defined)")
        parser.add_option('-C', '--category',
            help = "-C list' to see full list" )
        parser.add_option('--hidden',
            help="availability on host: 0=Available, 1=Hidden, 2=Available to family, 4=Available to friends/family.")
        parser.add_option('--release-all', action="store_true",
            help="ignore the released setting.")

  def add_more_option_defaults(self, parser):
      parser.set_defaults(category="Education")

if __name__ == '__main__':
    p=post()
    p.main()

