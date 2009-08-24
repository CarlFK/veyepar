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
    
    The script uses ffmpeg2theora to (optionally) convert video files to Ogg Theora.
    See http://v2v.cc/~j/ffmpeg2theora/.
    
    The script uses the blip.tv "REST Upload API". See http://blip.tv/about/api/.
    
    blip.tv uses item IDs to identify videos. For the video at
    http://blip.tv/file/123456, the item ID is "123456". The code refers to
    this ID as "video_id".
    
    Usage:
    @code
      blip_uploader.py [<video-id> [<filename>]]

      # Entirely interactive (you are prompted for all required information):
      blip_uploader.py
        
      # Upload alternate format to existing post:
      blip_uploader.py 123456 alternate_format.ogg
                    
      # Upload new video:
      blip_uploader.py "" new_video.mpg
    @endcode
"""

import getpass
import httplib
import mimetypes
import os
import re
import sys
import urllib2
import urlparse
from xml.dom.minidom import parseString
from xml.sax.saxutils import unescape

BLIP_UPLOAD_URL = "http://blip.tv/file/post"

MULTIPART_BOUNDARY = "-----------$$SomeFancyBoundary$$"

def PostMultipart(url, fields, files):
    """@brief Send multi-part HTTP POST request
    
    @param url POST URL
    @param fields A dict of {field-name: value}
    @param files A list of [(field-name, filename)]
    @return Status, reason, response (see httplib.HTTPConnection.getresponse())
    """
    content_type = 'multipart/form-data; boundary=%s' % MULTIPART_BOUNDARY

    # gather all the data (except for the actual file) into:
    # fieldsdata - string of "field1:value1\nfield2:value2\n..."
    # filedatas - list of tuples: [(metadata1, filename1),(m2,f2)...]
    # footdata - string, final "\n--file delimiter--\n"
    data = []
    for field_name, value in fields.iteritems():
        data.append('--' + MULTIPART_BOUNDARY)
        data.append('Content-Disposition: form-data; name="%s"' % field_name)
        data.append('')
        data.append(value)
    fieldsdata="\r\n".join(data)
    filedatas=[]
    for (field_name, filename) in files:
        data=['']
        data.append('--' + MULTIPART_BOUNDARY)
        data.append('Content-Disposition: form-data; name="%s"; filename="%s"'
                    % (field_name, filename))
        data.append('Content-Type: %s' % GetMimeType(filename))
        data.append('')
        data.append('')
        filedatas.append(['\r\n'.join(data),filename])
    footdata='\r\n--' + MULTIPART_BOUNDARY + '--\r\n'

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
    for filedata, filename in filedatas:
        h.send(filedata)
        f = open(filename,'rb')
        block=f.read(10000)
        while block:
            h.send(block)
            block=f.read(10000)
    h.send(footdata)

    response = h.getresponse()
    return response.status, response.reason, response.read()    

def GetMimeType(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def Upload(video_id, username, password, title, description, filename):
    """@brief Upload to blip.tv
    
    @param video_id Either the item ID of an existing post or None to upload
        a new video
    @param username, password
    @param title New title of the post
    @param description New description of the post
    @param filename Filename of the video to upload (if a @a video_id is specified),
        this file is uploaded as an additional format to the existing post)
    @return Response data
    """
    fields = {
        "post": "1",
        "skin": "xmlhttprequest",
        "userlogin": "%s" % username,
        "password": "%s" % password,
        "item_type": "file",
        "title": "%s" % title.encode("utf-8"),
        "description": "%s" % description.encode("utf-8"),
        }
    if video_id:    # update existing
        fields["id"] = "%s" % video_id
        file_field = "file1"
    else:           # new post
        file_field = "file"
    if filename:
        fields[file_field + "_role"] = "Web"
        files = [(file_field, filename)]
    else:
        files = []
    
    print "Posting to", BLIP_UPLOAD_URL
    print "Please wait..."
    status, reason, response = PostMultipart(BLIP_UPLOAD_URL, fields, files)
    print "Done."

    return response
        
def AskForVideoId():
    video_id = None
    while video_id is None:
        video_url = raw_input("Enter blip.tv video ID or URL\n  (e.g., "
                              "'123456' or 'http://blip.tv/file/123456'),\n"
                              "  or press RETURN to upload a new video: ")
        if not video_url:
            return None
        m = re.match(r"[^\d]*(\d+).*", video_url)
        if m:
            video_id = m.group(1)
        else:
            print "Invalid format"
    return video_id

def AskYesNo(question, default=True):
    while True:
        if default == True:
            options = "[Y/n]"
        else:
            options = "[y/N]"
        yes_no = raw_input(question + " " + options + " ")
        if not yes_no:
            return default
        elif yes_no in ["Y", "y"]:
            return True
        elif yes_no in ["N", "n"]:
            return False
            
def GetTextFromDomNode(node):
    rc = ""
    for n in node.childNodes:
        if n.nodeType == node.TEXT_NODE or n.nodeType == node.CDATA_SECTION_NODE:
            rc = rc + n.data
    return rc

def GetVideoInfo(video_id):
    """@brief Return information about the video
    
    @param video_id blip.tv item ID
    @return A tuple of
        @a title (string),
        @a description (string),
        @a link (URL to video as a string),
        @a embed_code (HTML <embed> code as a string),
        @a embed_id (the part of the <embed> code that's used with the Drupal filter,
            e.g., "AbCcKIuEBA"),
        @a existing_mime_types (a dict of {mime_type: list_of_file_urls}
            containing the URLs that are currently part of the post)
    """
    url = 'http://blip.tv/file/%(video_id)s?skin=rss' % locals()
    print "Loading", url, "..."
    xml_code = urllib2.urlopen(url).read()
    rss = parseString(xml_code)
    channel = rss.getElementsByTagName("channel")[0]
    item = channel.getElementsByTagName("item")[0]
    title = GetTextFromDomNode(item.getElementsByTagName("title")[0])
    description = unescape(
        GetTextFromDomNode(item.getElementsByTagName("blip:puredescription")[0]))
    link = GetTextFromDomNode(item.getElementsByTagName("link")[0])
    embed_code = GetTextFromDomNode(item.getElementsByTagName("media:player")[0])
    embed_id = None
    m = re.search(r"http://blip.tv/play/(\w+)", embed_code)
    if m:
        embed_id = m.group(1)

    existing_mime_types = {}
    media_group = item.getElementsByTagName("media:group")[0]
    for content in media_group.getElementsByTagName("media:content"):
        existing_mime_types.setdefault(content.attributes["type"].value, []).append(
            content.attributes["url"].value)
        
    return title, description, link, embed_code, embed_id, existing_mime_types

def DisplayVideoInfo(title, link, embed_code, embed_id, existing_mime_types):
    print "Title           =", title
    print "Link            =", link
    if embed_id:
        print "Embed ID        =", embed_id
    else:
        print "Embed ID        = <The video hasn't been converted to Flash yet>"
    if existing_mime_types:
        print "Files           ="
        for urls in existing_mime_types.itervalues():
            for url in urls:
                print "    " + url

def ConvertToOggTheora(filename):
    out_filename = os.path.splitext(filename)[0] + os.extsep + "ogg"
    cmd = 'ffmpeg2theora -o "%(out_filename)s" "%(filename)s"' % locals()
    print "Running", cmd, "..."
    exit_code = os.system(cmd)
    if exit_code:
        print "Error: Command returned with code %r" % (exit_code,)
        sys.exit(1)
    return out_filename

def GetDescription(default):
    if os.path.exists("description.txt"):
        print ''
        print 'Taking description from file "description.txt"...'
        default = open("description.txt").read()
    print "Current description:\n  {{{%s}}}" % default
    print ""
    desc = raw_input(
        'Type a new one-line description or press RETURN to keep the current one\n'
        '  (If you need more than one line, press Ctrl+C to abort,\n'
        '  create a file named "description.txt" and run again): ')
    return desc or default

def Main():
    if len(sys.argv) < 2:
        video_id = AskForVideoId()
    else:
        video_id = sys.argv[1]

    if video_id:
        print ""
        (title, description, link,
         embed_code, embed_id, existing_mime_types) = GetVideoInfo(video_id)
    
        print ""
        print "Video Info:"
        DisplayVideoInfo(title, link, embed_code, embed_id, existing_mime_types)
        print ""
    
        if not AskYesNo('Is this the video you want to modify?', True):
            sys.exit(0)
    else:
        print ""
        title = raw_input("Title of your new post: ")
        description = ""
        existing_mime_types = {}
        
    if len(sys.argv) < 3:
        print ""
        filename = raw_input("Filename of video to upload (leave blank if "
                             "you want to change the description only): ")
    else:
        filename = sys.argv[2]

    if filename:
        mime_type = GetMimeType(filename)
        if mime_type != "application/ogg":
            print ""
            if AskYesNo('The file "%(filename)s" is of type "%(mime_type)s".\n'
                        'Do you wish to convert it to Ogg Theora?' % locals(),
                        True):
                print ""
                filename = ConvertToOggTheora(filename)
                mime_type = "application/ogg"
                print ""
                
        print ""
        if mime_type in existing_mime_types:
            if not AskYesNo('A video of type "%(mime_type)s" was already uploaded.\n'
                            'Would you still like to upload the file "%(filename)s"?'
                            % locals(),
                            False):
                filename = None
    else:
        filename = None
    
    description = GetDescription(description)
    
    print ""
    print "Ready to post."
    print "- Upload file:", filename
    print "- Set title to:", title
    print "- Set description to:\n  {{{%s}}}" % description
    print ""
    if AskYesNo("Is this okay?", True):
        print ""
        username = raw_input("blip.tv Username: ")
        pwd = getpass.getpass("blip.tv Password: ")
        print ""
        response = Upload(video_id, username, pwd, title, description, filename)
        print ""
        print "Server response:\n  {{{%s}}}" % response
        
    return 0

if __name__ == "__main__":
    sys.exit(Main())
