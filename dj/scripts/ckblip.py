#!/usr/bin/python

# ckblip.py
# checks metadata on blib
# like 'is there a flash version?'
# or 'if a format is not on blip, is it local?'
# and maybe upload it.


import os

import blip_uploader
from post import roles
import pw

from process import process

from main.models import Episode

class ckblip(process):

  def post(self, ep, file_types_to_upload):

    blip_cli=blip_uploader.Blip_CLI()

    files = []
    for i,ext in enumerate(file_types_to_upload):
        i+=10
        fileno=str(i) if i else ''
        role=roles.get(ext,'extra')
        src_pathname = os.path.join( self.show_dir, ext, "%s.%s"%(ep.slug,ext))
        print (fileno,role,src_pathname)
        files.append((fileno,role,src_pathname))

    src_pathname = '%s/ogv/%s.ogv'%(self.show_dir, ep.slug)

    response = blip_cli.Upload(
            ep.target, pw.blip['user'], pw.blip['password'], files, {'title':ep.title})

    response_xml = response.read()
    print response_xml
    ep.comment += "\n%s\n" % response_xml


  def process_ep(self, ep):
    if self.options.verbose: print ep.id, ep.name, ep.target

    if ep.state == -1: return 
    """
    ext='flac'
    out_pathname = os.path.join(
        self.show_dir, ext, "%s.%s"%(ep.slug,ext))
    if ep.state>2 and not os.path.exists(out_pathname): print ep.id, 
    return True
    """

    type_map = (
             {'ext':'flv','mime':'video/x-flv'},
            )
    type_map = ({'ext':'ogv','mime':'video/ogg'},
             {'ext':'flv','mime':'video/x-flv'},
             {'ext':'m4v','mime':'video/x-m4v'},
             {'ext':'mp3','mime':'audio/mpeg'},)

    if ep.target:
        
        # Episode in veypar has been uploaded to blip,
        # use the local blip id and fetch the blip metadata.
        blip_cli=blip_uploader.Blip_CLI()
        blip_cli.debug = self.options.verbose

        xml_code = blip_cli.Get_VideoMeta(ep.target)
        if self.options.verbose: print xml_code

        blip_meta = blip_cli.Parse_VideoMeta(xml_code)
        files_on_blip = {}
        for content in blip_meta['contents']:
            files_on_blip[content['type']] = content
     
        if self.options.verbose: 
            print blip_meta['contents']
            print files_on_blip
# [u'video/ogg', u'audio/mpeg', u'video/x-flv', u'video/x-m4v']
    
        file_types_to_upload=[]    
        for t in type_map:
            pathname = os.path.join(
                    self.show_dir, t['ext'], "%s.%s"%(ep.slug,t['ext']))
            if t['mime'] in files_on_blip.keys():
                # there is somthing on blib
                # see if it is the same size as local copy
                if os.path.exists(pathname):
                    st = os.stat(pathname)
                    local_size = st.st_size
                    blip_size = int(files_on_blip[t['mime']]['fileSize'])
                    if local_size != blip_size:
                      file_types_to_upload.append(t['ext'])
                      if self.options.verbose:
                        print "file size mismatch."
                        # this can happen when a file needed to be re-encoded, 
                        # like when the cutlist is updated,
                        # or when blip gets happy whacking the .flv version 
                        print t
                        print "local:", local_size
                        print " blip:", blip_size
                        print
            else:
                # expected type not on blip
                # check for local copy
                if os.path.exists(pathname):
                    # local copy found, queue for upload
                    file_types_to_upload.append(t['ext'])
                else:
                    print "missing on blip and local",
                    print ep.id, t, pathname

        if file_types_to_upload: 
            if self.options.verbose: print file_types_to_upload    
        
            if self.options.test:
               print "self.post(%s,%s)"%(ep,file_types_to_upload)
            else:
               self.post(ep,file_types_to_upload)
    else:
        # episode not on blip, use post.py to set title, thumb, etc.
        print "post %s" % ep.id

    # ep.save()

    ret = True
    return ret


if __name__ == '__main__':
    p=ckblip()
    p.main()

