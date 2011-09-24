#!/usr/bin/python

# posts to blip.tv

import blip_uploader

import re
import os
import xml.etree.ElementTree

import pw
from process import process

from main.models import Show, Location, Episode, Raw_File, Cut_List

# this is here so ckblip can import roles
# http://wiki.blip.tv/index.php/Roles
    # old, works.. but Source looks better:    'ogv':"Web", 
roles={
        'mp4':{'description':"Master",'num':''},
        'flv':{'description':"Blip SD",'num':'1'},
        'ogv':{'description':"Web",'num':'2'},
        'm4v':{'description':"Portable (iPod)",'num':'4'},
        'ogg':{'description':"Portable (other)",'num':'5'},
        'mp3':{'description':"Audio-only",'num':'6'}
    }

class post(process):

  ready_state = 4

  def process_ep(self, ep):
    if self.options.verbose: print ep.id, ep.name
    if not ep.released:
        if self.options.verbose: print "not released:", ep.released
        return False

    loc = ep.location
    show = ep.show
    client = show.client

    descriptions = [ep.authors, ep.description, show.description, client.description]
    descriptions = [d for d in descriptions if d]
    description = "</p>\n".join(descriptions)
    description = "<br/>\n".join(description.split('\n'))

    blip_cli=blip_uploader.Blip_CLI()
    blip_cli.debug = self.options.verbose

    meta = {
        'title': ep.name,
        'description': description,
        }

# if .target is blank, a new episode will be created and .target set
# else it will use the id of the episode from a previous run. 
    video_id = ep.host_url

    tags = [ self.options.topics, client.slug, client.tags, show.slug, ep.tags ]
    meta['topics'] = ' '.join([tag for tag in tags if tag] )

    if ep.license: 
        license = ep.license
    elif self.options.license:
        license = self.options.license
    else:
        license = 'CC BY-SA'

    meta['license'] = {'CC BY-SA': '13'}[license]

    if self.options.rating:
        meta['content_rating'] = self.options.rating

    if self.options.category:
        meta['categories_id'] = self.options.category

    if self.options.hidden:
        meta['hidden'] = self.options.hidden

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

    
# the blip api gets kinda funky around multiple uploads
# so no surprise the code is kinda funky.
    files = []
    exts = self.options.upload_formats
# pull dv from the list
    exts = [e for e in exts if e != 'dv']
    has_master = False
    for ext in exts:
        role=roles.get(ext, {'description':"extra",'num':'9'})
        if role['description'] == 'Master': has_master = True
        fileno=role['num']
        role_desc = role['description']
        src_pathname = os.path.join( self.show_dir, ext, "%s.%s"%(ep.slug,ext))
        files.append([fileno,role_desc,src_pathname])

    if not video_id and not has_master: 
        # If this is a new upload (no id yet) blip needs one marked as master
        # if nothing is marked as master, mark the first one.
        # this seems like such a hack.
        files[0][0]=''
        files[0][1]='Master'

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
        # add the log to the list of files to be posted to blip
        files.append(("10","Captions",log_pathname))
        

    # username comes from options, client, first in pw.py
    # password always comes from pw.py
   
    # print "client blip_user", client.blip_user
    blip_user =  self.options.host_user if self.options.host_user \
                    else client.host_user if client.host_user \
                    else pw.host.keys()[0]
    # print "user", blip_user
    blip_pw = pw.blip[blip_user]

    if self.options.test:
        print 'test mode:'
        print 'blip_cli.Upload( video_id, user, pw, files, meta, thumb)'
        print video_id
        print 'files %s' % files
        print 'meta %s' % meta
        print 'thumb %s' % thumb
        print
    
        blipcmd = "./blip_uploader.py --fileno %s --role %s --filename %s" % (files[0])
        blipcmd += " --thumb %s" % thumb 
        for i in meta.items():
            blipcmd += " --%s %s" % i 
        print blipcmd 

    else:
   
        done=False
        while not done:
        
          response_obj = blip_cli.Upload(
            video_id, blip_user, blip_pw, files, meta, thumb)
          reponse_code = "%s: %s" % (
                  response_obj.status, response_obj.reason)
          response_xml = response_obj.read()

          if 'Guru Meditation' in response_xml:
            # buggy xml, will crash if we try to parse it.
            # xml bugged Sep 22 2010: http://support.blip.tv/requests/17356
            # self.options.verbose=True
            # solution is to just loop.
            done=False 
          else:
            done=True

        if self.options.verbose: print response_xml
        ep.comment += "\n%s\n%s\n" % (reponse_code,response_xml)
        ep.save()

        """<?xml version="1.0" encoding="UTF-8"?>
<otterResponses>
<response>
Your file called Test Episode #0 has been successfully posted.
<post_url>http://blip.tv/file/3734423</post_url>
</response>

</otterResponses>
"""

        """<?xml version="1.0" encoding="UTF-8"?>
<otterResponses>
<response>
	<notice>You are not authorized to edit this file.  If you believe you have reached this notice in error please contact your community administrator for assistance.</notice>
</response>

</otterResponses>

'<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n<html>\n  <head>\n    <title>503 Service Unavailable</title>\n  </head>\n  <body>\n    <h1>Error 503 Service Unavailable</h1>\n    <p>Service Unavailable</p>\n    <h3>Guru Meditation:</h3>\n    <p>XID: 1112821342</p>\n    <hr>\n    <p>Varnish cache server</p>\n  </body>\n</html>\n'

<otterResponses>
<response>
	<error>You must upload a file for your post</error>
	
		<hidden>1</hidden>
	
	<conversiontargets>
		<conversiontarget>
			<id>request_transcode_18</id>
			<name>m4v</name>
		</conversiontarget>
	
		<conversiontarget>
			<id>request_transcode_11</id>
			<name>mp3</name>
		</conversiontarget>
	</conversiontargets>
	
</response>

</otterResponses>


"""
# (02:37:51 PM) Juhaz: CarlFK, no. tree is the root element, it can't find itself, only children.

# there is no blip spec, but by looking at various returns:
# all have <otterResponses/response>
# if that has <post_url>, it was successfull
# otherwise look for the error message in <notice>

        tree = xml.etree.ElementTree.fromstring(response_xml)

        response = tree.find('response')
        post_url=response.find('post_url')
        if xml.etree.ElementTree.iselement(post_url):
            print post_url.text
            self.last_url = post_url.text # hook for tests so that it can be browsed
# <post_url>http://blip.tv/file/3734423</post_url>
            blip_id=post_url.text.split('/')[-1]
            if self.options.verbose:
                print "blip id:", blip_id
            ep.host_url = blip_id
            ep.comment += post_url.text
            self.log_info(response.text)
            ret=True
        else:
            # don't print it again if it was just printed 
            if not self.options.verbose: print response_xml
            ep.comment += "upload failed\n%s\n" % response_xml
            # look for the error message
            notice=response.find('notice')
            if xml.etree.ElementTree.iselement(notice):
                print "blip notice:", notice.text
                self.log_info(notice.text)
            ret=False
        ep.save()

        return ret

  def add_more_options(self, parser):
        parser.add_option('--blip-user', 
            help='blip.tv account name (pass stored in pw.py)')
        parser.add_option('--rating', 
            help="TV rating")
        parser.add_option('-T', '--topics',
            help="list of topics (user defined)")
        parser.add_option('-L', '--license',
            help="13 is Creative Commons Attribution-NC-ShareAlike 3.0\n"
            "'./blip_uploader.py -L list' to see full list" )
        parser.add_option('-C', '--category',
            help = "'./blip_uploader.py -C list' to see full list" )
        parser.add_option('--hidden',
            help="availability on blip.tv, 0=Available, 1=Hidden, 2=Available to family, 4=Available to friends/family.")


if __name__ == '__main__':
    p=post()
    p.main()

