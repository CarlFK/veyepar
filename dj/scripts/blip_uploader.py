#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2008 Michael Fötsch <foetsch@yahoo.com>
#    
#    Permission is hereby granted, free of charge, to any person obtaining
#    a copy of this software and associated documentation files (the
#    "Software"), to deal in the Software without restriction, including
#    without limitation the rights to use, copy, modify, merge, publish,
#    distribute, sublicense, and/or sell copies of the Software, and to
#    permit persons to whom the Software is furnished to do so, subject to
#    the following conditions:
#    
#    The above copyright notice and this permission notice shall be included
#    in all copies or substantial portions of the Software.
#    
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""@brief Upload videos to blip.tv or update blip.tv posts

    This script can be used to post videos to blip.tv, or to upload additional
    formats for existing posts, or to change the description of existing posts.
    
    The script uses the blip.tv "REST Upload API". See http://blip.tv/about/api/.
    blip.tv uses item IDs to identify videos. For the video at
    http://blip.tv/file/123456, the item ID is "123456". The code refers to
    this ID as "video_id".
    
    user/password will be prompted for if not passed.
    
    Usage:
    @code
      blip_uploader.py --help

      # Upload new video:
      blip_uploader.py -f new_video.mpg -t "My Great Video"

      # Upload alternate format to existing post:
      blip_uploader.py -v 123456 -f alternate_format.ogg -n 1 -r Web 
                    
    @endcode

    A Blip Episode can be created from just a Title and 1 File - a thumbnail
    will be generated and the default license applied. 
    Everything else is optional: 
        description, categories, additional formats, nsfw, topics

    This script will let you create and update Episodes.
    The creation requires a file, the script will create a Title 
    from the filename.  After that all attributes replace the current values.


"""

import optparse
import ConfigParser
import getpass
import httplib, socket
import mimetypes
import os
import datetime,time
import re
import sys
import urllib2
import urlparse
import xml.etree.ElementTree
import xml.dom.minidom 
import xml.sax.saxutils 

import cgi

def stot(seconds):
    # convert numeric seconds to hh:mm:ss time string
    s=seconds
    h,s=divmod(s,3600)
    m,s=divmod(s,60)
    t="%02i:%02i:%02i" % (h,m,s)
    return t


class Blip(object):

    BLIP_UPLOAD_URL = "http://blip.tv/file/post"
# While both URLs will currently work, future applications should use uploads.blip.tv. 
    
    MULTIPART_BOUNDARY = "-----------$$SomeFancyBoundary$$"

    debug=True

    def progress(self, current, total):
        """
        Hook method for letting the user see upload progress.
        """
        pass

    def GetMimeType(self, filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def PostMultipart(self, url, fields, files=[]):
        """@brief Send multi-part HTTP POST request
        
        @param url POST URL
        @param fields A dict of {field-name: value}
        @param files A list of [(field-name, filename)]
        @return Status, reason, response (see httplib.HTTPConnection.getresponse())
        """
        content_type = 'multipart/form-data; boundary=%s' % self.MULTIPART_BOUNDARY

        # gather all the data (except for the actual file) into:
        # fieldsdata - string of "field1:value1\nfield2:value2\n..."
        # filedatas - list of tuples: [(metadata1, filename1),(m2,f2)...]
        # footdata - string, final "\n--file delimiter--\n"
        data = []
        for field_name, value in fields.iteritems():
            data.append('--' + self.MULTIPART_BOUNDARY)
            data.append('Content-Disposition: form-data; name="%s"' % field_name)
            data.append('')
            data.append(value.encode("utf-8"))
        fieldsdata="\r\n".join(data)
        filedatas=[]
        for (field_name, filename) in files:
            data=['']
            data.append('--' + self.MULTIPART_BOUNDARY)
            data.append('Content-Disposition: form-data; name="%s"; filename="%s"'
                        % (field_name, filename))
            data.append('Content-Type: %s' % self.GetMimeType(filename))
            data.append('')
            data.append('')
            filedatas.append(['\r\n'.join(data),filename])
        footdata='\r\n--' + self.MULTIPART_BOUNDARY + '--\r\n'

        # sum up the size of the 3 datas, including the file size
        datalen = len(fieldsdata)
        for filedata, filename in filedatas:
            datalen += len(filedata)
            datalen += os.stat(filename).st_size
        datalen += len(footdata)

        # open the connection, send the headers (not part of datas)
        host, selector = urlparts = urlparse.urlsplit(url)[1:3]
        h = httplib.HTTPConnection(host)
        h.putrequest("POST", selector)
        h.putheader("content-type", content_type)
        h.putheader("content-length", datalen)
        h.endheaders()

        # send the datas
        if self.debug: print fieldsdata.__repr__()
        if self.debug: print fieldsdata
        self.start_time = datetime.datetime.now()
        h.send(fieldsdata)
        bytes_sent = len(fieldsdata)
        for filedata, filename in filedatas:
            if self.debug: print "%s (%s)" % (filedata.__repr__(), filename)
            if self.debug: print "%s (%s)" % (filedata, filename)
            h.send(filedata)
            bytes_sent += len(filedata)
            f = open(filename,'rb')
            block_size=15000
            block=f.read(block_size)
            while block:
                h.send(block)
                bytes_sent += len(block)
                self.progress(bytes_sent,datalen)
                # time.sleep(.06)
                block=f.read(block_size)
        if self.debug: print footdata.__repr__()
        h.send(footdata)
        bytes_sent += len(footdata)
        self.progress(bytes_sent,datalen)

        response = h.getresponse()
        return response

    def Upload(self, video_id, username, password, files, meta={}, thumbname=None):
        """@brief Upload to blip.tv
        
        @param video_id Either the item ID of an existing post or None to create
            a new Episode.
        @param username, password
        @param files List of Filenames and Roles of videos to upload 
        @param meta['foo'] New foo of the post (title, description, etc)
        @thumbname New thumbnail filename    
        @return Response data
        
        """
        fields = {
            "post": "1",
            "skin": "xmlhttprequest",
            "userlogin": username,
            "password": password,
            "item_type": "file",
            }

        if video_id:    # update existing
            fields["id"] = video_id

        # add in additional metadata
        fields.update(meta)

        # extract out the file number and roles
        # example:
        # files = [ ('','Source','foo.ogg'), ('1','Web','foo.flv') ]
        # fields['file_role']='Source'
        # fields['file1_role']='Web'
        # files= [ ('file','foo.ogg'), ('file1','foo.flv') ]
        
        for no,role,filename in files:
            fields["file%s" % no + "_role"] = role
        files = [("file%s" % no, filename) for no,role,filename in files]

        if thumbname:
            files.append(("thumbnail",thumbname))

        done=False
        while not done:
          try:
            response = self.PostMultipart(self.BLIP_UPLOAD_URL, fields, files)
            done=True

          except socket.error, e:
            print e
            # and try again...
            """
r/lib/python2.6/httplib.py", line 759, in send
    self.sock.sendall(str)
  File "<string>", line 1, in sendall
socket.error: [Errno 104] Connection reset by peer
"""

          except httplib.BadStatusLine:
            print e
            # and try again...
            """
  File "/usr/lib/python2.6/httplib.py", line 391, in begin
    version, status, reason = self._read_status()
  File "/usr/lib/python2.6/httplib.py", line 355, in _read_status
    raise BadStatusLine(line)
httplib.BadStatusLine
"""

        return response

    def Get_Licenses(self):
        """
        Get the list of licenses blip crrently supports.
        """
        url = 'http://www.blip.tv/?section=licenses&cmd=view&skin=api'
        xml_code = urllib2.urlopen(url).read()
        return xml_code
           
    def Get_Categories(self):
        """
        Get the list of categories blip crrently supports.
        """
        url = 'http://www.blip.tv/?section=categories&cmd=view&skin=api'
        xml_code = urllib2.urlopen(url).read()
        return xml_code

    def Get_VideoMeta(self, video_id):
        """@brief Return information about the video
        
        @param video_id blip.tv item ID
        @return xml of all the metadata.
        """
        url = 'http://blip.tv/file/%s?skin=rss' % video_id
        if self.debug: print url
        xml_code = urllib2.urlopen(url).read()
        return xml_code

    def Get_TextFromDomNode(self, node):
        rc = ""
        for n in node.childNodes:
            if n.nodeType in [node.TEXT_NODE, node.CDATA_SECTION_NODE]:
                rc += n.data
        return rc

    def Parse_VideoMeta(self, video_xml):
        """@brief Return information about the video
        
        @param video_xml xml about an Episode from blip.tv 
        @return A dictionary with keys:
            @a title (string),
            @a description (string),
            @a link (URL to video as a string),
            @a embed_code (HTML <embed> code as a string),
            @a embed_id (the part of the <embed> code that's used with the Drupal filter,
                e.g., "AbCcKIuEBA"),
            @a existing_mime_types (a dict of {mime_type: list_of_file_urls}
                containing the URLs that are currently part of the post)
        """
        meta={}
        rss = xml.dom.minidom.parseString(video_xml)
        channel = rss.getElementsByTagName("channel")[0]
        item = channel.getElementsByTagName("item")[0]
        meta['title'] = self.Get_TextFromDomNode(item.getElementsByTagName("title")[0])
        meta['description'] = xml.sax.saxutils.unescape(
            self.Get_TextFromDomNode(item.getElementsByTagName("blip:puredescription")[0]))
        meta['link'] = self.Get_TextFromDomNode(item.getElementsByTagName("link")[0])
        meta['embed_code'] = self.Get_TextFromDomNode(item.getElementsByTagName("media:player")[0])
        
        existing_mime_types = {}
        contents = []
        media_group = item.getElementsByTagName("media:group")[0]
        for content in media_group.getElementsByTagName("media:content"):
            existing_mime_types.setdefault(content.attributes["type"].value, []).append( content.attributes["url"].value)
            contents.append({
               'url': content.attributes["url"].value,
               'type': content.attributes["type"].value,
               'fileSize': content.attributes["fileSize"].value,
               'isDefault': content.attributes["isDefault"].value,
               'expression': content.attributes["expression"].value,
               'role': content.attributes["blip:role"].value,
               # 'acodec': content.attributes["blip:acodec"].value,
               })

        meta['existing_mime_types']=existing_mime_types
        meta['contents']=contents
            
        return meta

class Blip_CLI(Blip):

    """
    Demonstates use of the Blip class as a Command Line Interface.
    """

    def progress(self, current, total):
        """
        Displaies upload percent done, bytes sent, total bytes.
        """
        elapsed = datetime.datetime.now() - self.start_time 
        remaining_bytes = total-current
        if elapsed.seconds: 
            bps = current/elapsed.seconds
            remaining_seconds = remaining_bytes / bps
            eta = datetime.datetime.now() + datetime.timedelta(seconds=remaining_seconds)
            sys.stdout.write('\r%3i%%  %s of %s MB, %s kbps, elap/remain: %s/%s, eta: %s' 
              % (100*current/total, current/(1024**2), total/(1024**2), bps/1024, stot(elapsed.seconds), stot(remaining_seconds), eta.strftime('%H:%M:%S')))
        else: 
            sys.stdout.write('\r%3i%%  %s of %s bytes: remaining: %s' 
              % (100*current/total, current, total, remaining_bytes, ))

    def List_Licenses(self):
        """
        Print the list of licenses blip crrently supports.
        """
        xml_code = self.Get_Licenses()
        tree = xml.etree.ElementTree.fromstring(xml_code)
        for node in tree.findall('payload/license'):
            print node.find('id').text, node.find('name').text
        return
           
    def List_Categories(self):
        """
        Print the list of categories blip crrently supports.
        """
        xml_code = self.Get_Categories()
        tree = xml.etree.ElementTree.fromstring(xml_code)
        for node in tree.findall('payload/category'):
            print node.find('id').text, node.find('name').text
        return

    def List_VideoMeta(self, video_id):
        print "Loading..."
        xml_code = self.Get_VideoMeta(video_id)
        # print xml_code
        info = self.Parse_VideoMeta(xml_code)
        # print info
        print "Title           =", info['title']
        print "Description     =", info['description']
        print "Link            =", info['link']
        if info['embed_code'].strip():
            print "Embed code      =", info['embed_code']
        else:
            print "Embed code      = <The video hasn't been converted to Flash yet>"
        print "Files:"
        for role,urls in info['existing_mime_types'].items():
            print role
            for url in urls:
                print "\t%s" % url
        print info['contents']

    def parse_args(self):

        parser = optparse.OptionParser()

        # hardcoded defauts
        parser.set_defaults(role='Source')
        parser.set_defaults(fileno='')
        parser.set_defaults(thumb=None)
        parser.set_defaults(license='13')

        # read from config file, overrides hardcoded
        """
        >>> open('blip_uploader.cfg').read()
        '[global]\ncategory=7\nlicense=13\ntopics=test\n'
        >>> config.read('blip_uploader.cfg')
        >>> config.items('global')
        [('category', '7'), ('topics', 'test'), ('license', '13')]
        """

        config = ConfigParser.RawConfigParser()
        files=config.read(['blip_uploader.cfg', 
                    os.path.expanduser('~/blip_uploader.cfg')])
        if files:
            d=dict(config.items('global')) 
            parser.set_defaults(**d) 
            if d.get('verbose'): print "using config file(s):", files

        # command line options override config file
        parser.add_option('-f', '--filename', 
            help = 'Filename of media to upload')
        parser.add_option('-r', '--role', 
            help = 'Role for this file.  examples: Source, Web, Cell Phone.')
        parser.add_option('-n', '--fileno', 
            help = 'format number - used when uploading alternative format.')
        parser.add_option('-b', '--thumb',
            help = 'Filename of thumbnail to upload')
        parser.add_option('-t', '--title',
            help = "defaults to filename for new blip episodes (no video id.)")
        parser.add_option('-d', '--description',
            help='description, or @filename of description')
        parser.add_option('-T', '--topics', 
            help="list of topics (user defined)")
        parser.add_option('-L', '--license', 
            help="13 is Creative Commons Attribution-NC-ShareAlike 3.0\n"
            "'list' to see full list" )
        parser.add_option('-C', '--category',
            help = "7 Technology, 10 Conferences\n'list' to see full list" )
        parser.add_option('--hidden',
            help="availability on blip.tv, 0=Available, 1=Hidden, 2=Available to family, 4=Available to friends/family.")
        parser.add_option('-i', '--videoid',
            help="ID of existing blip episode (for updating.)")
        parser.add_option('-m', '--meta', action="store_true",
            help="List metadata about an exising episode and exit (all update options are ignored.)")
        parser.add_option('-u', '--username')
        parser.add_option('-p', '--password')
        parser.add_option('-v', '--verbose', action="store_true" )
        parser.add_option('--test', action="store_true" )

        options, args = parser.parse_args()
        return options, args

    def Main(self):

        options, args = self.parse_args()
     
        meta={} # metadata about the post: title, licence...
        # keys defined http://wiki.blip.tv/index.php/REST_Upload_API

        video_id = options.videoid 

        if options.meta:
            if video_id:
                self.List_VideoMeta(video_id)
                return 0
            else:
                print "You must suply a video ID to get info about it."
                return 1

        # this gets messy because there is metadata about the episode,
        # and also metadata about each file.
        # the command line options only support one file at a time
        # but the Upload func supports a list of files/roles.
        # These next few lines make the list out of the single file/role.
        files = []
        if options.filename:
           files+= [(options.fileno, options.role, options.filename)]

        if options.title:
            meta['title'] = cgi.escape(options.title.encode("utf-8"))

        if options.description:
            # getting a description from either command line or read from file.
            # both are an IO boundary, so decode on the way in
            # if options.description[0]=='@':
            #     meta['description'] = open(options.description[1:]).read()
            if options.description.startswith('@'):
                # read description from file
                meta['description'] = open(options.description[1:]).read()
            else:
                meta['description'] = options.description
            # input is utf-8 encoded becase I say.
            meta['description'] = meta['description'].decode("utf-8")
            # I tink this converts < to &lt; not sure if that is a good thing.
            meta['description'] = cgi.escape( meta['description'] )
        
        if options.topics:
            meta['topics'] = options.topics

        if options.license:
            if options.license=='list':
                self.List_Licenses()
                return 
            else:
                meta['license'] = options.license

        if options.category:
            if options.category=='list':
                self.List_Categories()
                return 
            else:
                meta['categories_id'] = options.category

        if not video_id:
            # no video_id = new Episode
            if not files:
                print "Must either supply video_id or filename"
                return 1
            if not options.title:
                # make a title from the filename (strip the path, leave the ext.)
                meta['title'] = os.path.basename(options.filename)

        if options.hidden:
            meta['hidden']=options.hidden

      
        username = options.username if options.username \
            else raw_input("blip.tv Username: ")
        pwd = options.password if options.password \
            else getpass.getpass("blip.tv Password: ")

        self.debug=options.verbose
        if options.verbose: print meta

        if options.test:
            print "Upload(video_id, username, pwd, files, meta, options.thumb)"
            print "video_id:", video_id
            print "username:", username 
            print "pwd", pwd, 
            print "files", files, 
            print "meta", meta 
            print "options.thumb", options.thumb
        else:
            response = self.Upload(video_id, username, pwd, files, meta, options.thumb)
            response_xml = response.read()
            if options.verbose: print response_xml
            tree = xml.etree.ElementTree.fromstring(response_xml)
            rep_node=tree.find('response')
            print rep_node.text,
            posturl_node=rep_node.find('post_url')
            print posturl_node.text
            
        return 0

if __name__ == "__main__":
    blip_cli=Blip_CLI()
    sys.exit(blip_cli.Main())

