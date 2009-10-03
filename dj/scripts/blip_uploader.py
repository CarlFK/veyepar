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
import getpass
import httplib
import mimetypes
import os
import re
import sys
import urllib2
import urlparse
import xml.etree.ElementTree
import xml.dom.minidom 
import xml.sax.saxutils 

import cgi


class Blip(object):

    BLIP_UPLOAD_URL = "http://blip.tv/file/post"
    
    MULTIPART_BOUNDARY = "-----------$$SomeFancyBoundary$$"

    def progress(self, current, total):
        """
        Hook method for letting the user see upload progress.
        """
        pass

    def GetMimeType(self, filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def PostMultipart(self, url, fields, files):
        """@brief Send multi-part HTTP POST request
        
        @param url POST URL
        @param fields A dict of {field-name: value}
        @param files A list of [(field-name, filename)]
        @param progress A callback to update progress - like percent done.
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
            data.append(value)
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
        h.send(fieldsdata)
        bytes_sent = len(fieldsdata)
        for filedata, filename in filedatas:
            h.send(filedata)
            bytes_sent += len(filedata)
            f = open(filename,'rb')
            block=f.read(10000)
            while block:
                h.send(block)
                bytes_sent += len(block)
                self.progress(bytes_sent,datalen)
                block=f.read(10000)
        h.send(footdata)

        response = h.getresponse()
        return response

    def Upload(self, video_id, username, password, files, meta, thumbname=None):
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
            "userlogin": "%s" % username,
            "password": "%s" % password,
            "item_type": "file",
            }

        if video_id:    # update existing
            fields["id"] = "%s" % video_id

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

        print "Posting to", self.BLIP_UPLOAD_URL
        print "Please wait..."
        response = self.PostMultipart(self.BLIP_UPLOAD_URL, fields, files)
        print "Done."

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

    def Get_VideoInfo(self, video_id):
        """@brief Return information about the video
        
        @param video_id blip.tv item ID
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
        url = 'http://blip.tv/file/%s?skin=rss' % video_id
        print url
        xml_code = urllib2.urlopen(url).read()
        return xml_code

    def Get_TextFromDomNode(self, node):
        rc = ""
        for n in node.childNodes:
            if n.nodeType == node.TEXT_NODE or n.nodeType == node.CDATA_SECTION_NODE:
                rc = rc + n.data
        return rc

    def Parse_VideoInfo(self, video_xml):
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
        media_group = item.getElementsByTagName("media:group")[0]
        for content in media_group.getElementsByTagName("media:content"):
            existing_mime_types.setdefault(content.attributes["type"].value, []).append(
                content.attributes["url"].value)
        meta['existing_mime_types']=existing_mime_types
            
        return meta

class Blip_CLI(Blip):

    """
    Demonstates use of the Blip class as a Command Line Interface.
    """

    def progress(self, current, total):
        """
        Displaies upload percent done, bytes sent, total bytes.
        """
        sys.stdout.write('\r%3i%%  %s of %s bytes' % (100*current/total, current, total))

    def List_Licenses():
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

    def List_VideoInfo(self, video_id):
        print "Loading..."
        xml_code = self.Get_VideoInfo(video_id)
        info = self.Parse_VideoInfo(xml_code)
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

    def parse_args(self):
        parser = optparse.OptionParser()
        parser.add_option('-f', '--filename', 
            help = 'Filename of media to upload')
        parser.add_option('-r', '--role', default='Source',
            help = 'Role for this file.  examples: Source, Web, Cell Phone.')
        parser.add_option('-n', '--fileno', default='',
            help = 'format number - used when uploading alternative format.')
        parser.add_option('-t', '--title',
            help = "defaults to filename for new blip episodes (no video id.)")
        parser.add_option('-d', '--description',
            help='description, or @filename of description')
        parser.add_option('-T', '--topics',
            help="list of topics")
        parser.add_option('-l', '--license',
            help="13 is Creative Commons Attribution-NC-ShareAlike 3.0\n"
            "--license list to see full list" )
        parser.add_option('-c', '--category',
            help = "--categories list to see full list" )
        parser.add_option('-v', '--videoid',
            help="ID of existing blip episode (for updating.)")
        parser.add_option('-i', '--info', action="store_true",
            help="List info about an exising episode and exit (all update options are ignored.)")
        parser.add_option('-u', '--username')
        parser.add_option('-p', '--password')

        options, args = parser.parse_args()
        return options, args

    def Main(self):

        options, args = self.parse_args()

        meta={} # metadata about the post: title, licence...

        video_id = options.videoid 

        if options.info:
            if video_id:
                self.List_VideoInfo(video_id)
                return 0
            else:
                print "You must suply a video ID to get info about it."
                return 1

        if options.filename:
            # this gets messy because there is metadata about the episode,
            # and also metadata about each file.
            # the command line options only support one file at a time
            # but the Upload func supports a list of files/roles.
            # These next few lines make the list out of the single file/role.
            files = [(options.fileno, options.role, options.filename),]
        else:
            files = []

        if options.title:
            meta['title'] = cgi.escape(options.title.encode("utf-8"))

        if options.description:
            if options.description[0]=='@':
                meta['description'] = open(options.description[1:]).read()
            else:
                meta['description'] = options.description
            meta['description'] = cgi.escape(meta['description'].encode("utf-8"))
        
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
                meta['categorie_id'] = options.category

        if not video_id:
            # no video_id = new Episode
            if not files:
                print "Must either supply video_id or filename"
                return 1
            if not options.title:
                # make a title from the filename (strip the path, leave the ext.)
                meta['title'] = os.path.basename(options.filename)

        username = options.username if options.username \
            else raw_input("blip.tv Username: ")
        pwd = options.password if options.password \
            else getpass.getpass("blip.tv Password: ")

        response = self.Upload(video_id, username, pwd, files, meta)
        response_xml = response.read()
        tree = xml.etree.ElementTree.fromstring(response_xml)
        rep_node=tree.find('response')
        print rep_node.text,
        posturl_node=rep_node.find('post_url')
        if posturl_node: print posturl_node.text
            
        return 0

if __name__ == "__main__":
    blip_cli=Blip_CLI()
    sys.exit(blip_cli.Main())

