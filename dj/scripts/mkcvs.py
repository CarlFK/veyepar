#!/usr/bin/python

# exports a cvs file of all epsides in a show

import urllib2
import xml.etree.ElementTree
import os

from csv import DictWriter

from process import process

from main.models import Client, Show, Location, Episode

class csv(process):

  ready_state = 4


  def blip_meta(self, video_id):
        """@brief Return information about the video
        
        @param video_id blip.tv item ID
        @return xml of all the metadata.
        """
        url = 'http://blip.tv/file/%s?skin=rss' % video_id
        # print url
        xml_code = urllib2.urlopen(url).read()
        # open('foo.xml','w').write(xml_code)
        return xml_code

  def get_embed(self, blip_xml):
     tree = xml.etree.ElementTree.fromstring(blip_xml)
     chan=tree.findall('channel')[0]
     item=chan.findall('item')[0]
     g=item.findall('{http://search.yahoo.com/mrss/}player')[0]
     embed=g.text
  
  def get_media(self, blip_xml, role="Source"):
     tree = xml.etree.ElementTree.fromstring(blip_xml)
     chan=tree.findall('channel')[0]
     item=chan.findall('item')[0]
     g=item.findall('{http://search.yahoo.com/mrss/}group')[0]
     ms = g.findall('*')
     roles=[dict(m.items())['{http://blip.tv/dtd/blip/1.0}role'] for m in ms]
     # print roles
     try:
        ri=roles.index(role)
     except ValueError:
        ri=0
     m=ms[ri]
     url = m.attrib['url']
     return url


  def process_eps(self,episodes):
    """ Export episodes metadata. """

    if self.options.basename:
          basename = self.options.basename
    else:
# name the file after the client_show of the first episode
# normaly a file will not span client or show
          ep=episodes[0]
          show=ep.location.show
          client=show.client
          self.show_dir = os.path.join(
              self.options.mediadir,client.slug,show.slug)
          basename = "%s_%s" % (client.slug,show.slug)

    csv_pathname = os.path.join( self.show_dir, "txt", basename+".csv" )
    txt_pathname = os.path.join( self.show_dir, "txt", basename+".txt" )
    html_pathname = os.path.join( self.show_dir, "txt", basename+".html" )

    if self.options.verbose: 
        print "filenames:\n%s\n%s\n%s" % (
            csv_pathname, txt_pathname, html_pathname )

# setup csv 
    fields="id state name primary comment blip source".split()
    csv = DictWriter(open(csv_pathname, "w"),fields, extrasaction='ignore')
    # write out field names
    csv.writerow(dict(zip(fields,fields)))

# setup txt
    txt=open(txt_pathname, "w")

# setup html (not full html, just some snippits)
    html=open(html_pathname, "w")

    # write out episode data
    for ep in episodes:
        row=ep.__dict__
        if self.options.verbose: print row

        comment=row['comment'].strip()
        blip_id=comment[comment.find('/file/')+6:]
        url = "http://carlfk.blip.tv/file/%s"%blip_id

        blip_xml=self.blip_meta(blip_id)

        embed=self.get_embed(blip_xml)
        row['blip']=embed

        media=self.get_media(blip_xml)
        row['source']=media

        csv.writerow(row)
        txt.write("%s %s\n" % (url,row['name']))
        print("%s %s\n" % (url,row['name']))
        html.write('<a href="%s">%s</a>\n%s\n'%(
            url,row['name'],row['blip']))

  def add_more_options(self, parser):
        parser.add_option('-f', '--basename', 
            help='base of output filename' )

if __name__ == '__main__':
    p=csv()
    p.main()
