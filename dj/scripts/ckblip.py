#!/usr/bin/python

# ckblip.py
# checks metadata on blib
# like 'is there a flash version?'
# or 'if a format is not on blip, is it local?'
# and maybe upload it.

# and maybe delete it:
# if the .fvl is not the same file size as the local copy on disk,
# delete the one on blip.

import os
import xml.etree.ElementTree

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
        # print (fileno,role,src_pathname)
        files.append((fileno,role,src_pathname))

    src_pathname = '%s/ogv/%s.ogv'%(self.show_dir, ep.slug)

    response = blip_cli.Upload(
            ep.target, pw.blip['user'], pw.blip['password'], files, {'title':ep.title})

    response_xml = response.read()
    # print response_xml
    ep.comment += "\n%s\n" % response_xml

  def delete_from_blip(self, episode_id, file_id, user, password, reason):
# http://blip.tv/file/delete/Pyohio-GettingToKnowMongoDBUsingPythonAndIronPython664.flv?reason="just cuz."
#http://blip.tv/?cmd=delete;id=Veyepar_test-TestEpisode0760.ogv;s=file;undelete=
    print "http://blip.tv/file/" + episode_id
    print "delete:", file_id
    return 

    # user,password = ('veyepar_test','bdff6680')
    fields = {
            # "post": "1",
            "cmd":"delete",
            "skin": "xmlhttprequest",
            "userlogin": user,
            "password": password,
            "item_type": "file",
            "reason": reason,
            "id": file_id
            }

    blip_cli=blip_uploader.Blip_CLI()
    # blip_delete_url="http://blip.tv/file/delete/%s" % file_id
    blip_delete_url="http://blip.tv/"
    # print blip_delete_url
    response = blip_cli.PostMultipart(blip_delete_url, fields)
 
    response_xml = response.read()
    if self.options.verbose: print response_xml
    tree = xml.etree.ElementTree.fromstring(response_xml)
    response = tree.find('response')
    if self.options.verbose: print "response.txt", response.text
    notice=response.find('notice')
    if xml.etree.ElementTree.iselement(notice):
        print "notice.text", notice.text

    return response

 
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
             {'ext':'ogv','mime':'video/ogg'},
             {'ext':'flv','mime':'video/x-flv'},
            # {'ext':'m4v','mime':'video/x-m4v'},
            # {'ext':'mp3','mime':'audio/mpeg'},)
            )

    if ep.target:
        
        # Episode in veypar has been uploaded to blip,
        # use the local blip id and fetch the blip metadata.
        blip_cli=blip_uploader.Blip_CLI()
        blip_cli.debug = self.options.verbose
        
        xml_code = blip_cli.Get_VideoMeta(ep.target)
        if self.options.verbose: print xml_code

        blip_meta = blip_cli.Parse_VideoMeta(xml_code)

        for t in type_map:
            pathname = os.path.join(
                    self.show_dir, t['ext'], "%s.%s"%(ep.slug,t['ext']))
            if os.path.exists(pathname):
                st = os.stat(pathname)
                local_size = st.st_size
                for content in blip_meta['contents']:
                    if self.options.verbose: print content
                    if content['type']==t['mime']:
                        blip_size = int(content['fileSize'])
                        if local_size != blip_size:
                            file_id = os.path.basename(content['url'])
                            user= \
  ep.show.client.blip_user if ep.show.client.blip_user \
  else self.options.blip_user
                            password= pw.blip[user]
                            ret=self.delete_from_blip(ep.target, file_id,
                                user, password, 'old version')
                        else:
                            ep.state=5
                            ep.save()
                            if self.options.verbose: print t['ext'], "right size"
    ret = True
    return ret
    """

        # code left over from PyCon10 audit.
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
    """


if __name__ == '__main__':
    p=ckblip()
    p.main()

