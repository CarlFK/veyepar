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
     """
     role="Web"
     g=item.findall('{http://search.yahoo.com/mrss/}group')[0]
     ms = g.findall('*')
     roles=[dict(m.items())['{http://blip.tv/dtd/blip/1.0}role'] for m in ms]
     # print roles
     try:
        ri=roles.index(role)
     except ValueError:
        ri=0
     # print ms[ri]
     embed=xml.etree.ElementTree.tostring(ms[ri])
     # print embed
     """
     return embed

  def one_show(self, show):
    """ Export all the episodes of a show. """
    
    filename = os.path.join( self.show_dir, "txt", 
        "%s_%s.csv" % (show.client.slug,show.slug))

    if self.options.verbose: print "filename: %s" % (filename)
    fields="id state name primary comment".split()
    if self.options.get_blip:
        fields+=['blip']

    writer = DictWriter(open(filename, "w"),fields, extrasaction='ignore')
    # write out field names
    writer.writerow(dict(zip(fields,fields)))

    # write out episode data
    for ep in Episode.objects.filter(
		location__show=show, state=4).order_by('sequence'):
        row=ep.__dict__
        if self.options.get_blip:
            comment=row['comment'].strip()

            blip_id=comment[comment.find('/file/')+6:]
            blip_xml=self.blip_meta(blip_id)
            embed=self.get_embed(blip_xml)
            row['blip']=embed
            if self.options.verbose: 
                print '<a href="'
                print "http://carlfk.blip.tv/file/%s"%blip_id
                print '">'
                print row['name']
                print '</a>'
                print embed
                print
        writer.writerow(row)

  def add_more_options(self, parser):
    parser.add_option('--get-blip',action='store_true',
        help='get the blip metadata' )


if __name__ == '__main__':
    p=csv()
    p.main()
