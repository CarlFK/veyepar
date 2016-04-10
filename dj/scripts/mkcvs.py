#!/usr/bin/python

# exports a cvs file of all epsides in a show

import urllib.request, urllib.error, urllib.parse
import xml.etree.ElementTree
import os
import pprint

from csv import DictWriter
import json

# import blip_uploader

from process import process

from main.models import Client, Show, Location, Episode

class csv(process):

  # ready_state = 6

  def blip_meta(self, video_id):
        """@brief Return information about the video
        
        @param video_id blip.tv item ID
        @return xml of all the metadata.
        """
        url = 'http://blip.tv/file/%s?skin=rss' % video_id
        # print url
        xml_code = urllib.request.urlopen(url).read()
        # open('foo.xml','w').write(xml_code)
        return xml_code

  def get_showpage(self, blip_xml):
     tree = xml.etree.ElementTree.fromstring(blip_xml)
     chan=tree.findall('channel')[0]
     item=chan.findall('item')[0]
     g=item.findall('{http://blip.tv/dtd/blip/1.0}showpage')[0]
     showpage=g.text
     return showpage
 
  def get_embed(self, blip_xml):
     tree = xml.etree.ElementTree.fromstring(blip_xml)
     chan=tree.findall('channel')[0]
     item=chan.findall('item')[0]
     g=item.findall('{http://search.yahoo.com/mrss/}player')[0]
     embed=g.text
     embed=embed.strip(' \n')
     return embed
  
  def get_media(self, blip_xml, role="Source"):
     tree = xml.etree.ElementTree.fromstring(blip_xml)
     chan=tree.findall('channel')[0]
     item=chan.findall('item')[0]
     g=item.findall('{http://search.yahoo.com/mrss/}group')[0]
     ms = g.findall('*')
     if role=='*':
         ret = [ m.attrib['url'] for m in ms ]
     else:
         roles=[dict(list(m.items()))['{http://blip.tv/dtd/blip/1.0}role'] for m in ms]
         # print roles
         try:
            ri=roles.index(role)
         except ValueError:
            ri=0
         m=ms[ri]
         ret = m.attrib['url']

     return ret


  def process_eps(self,episodes):
    """ Export episodes metadata. """

    if self.options.basename:
          basename = self.options.basename
    else:
# name the file after the client_show of the first episode
# normaly a file will not span client or show
          ep=episodes[0]
          show=ep.show
          client=show.client
          self.set_dirs(show)
          basename = "%s_%s" % (client.slug,show.slug)

    json_pathname = os.path.join( self.show_dir, "txt", basename+".json" )
    csv_pathname = os.path.join( self.show_dir, "txt", basename+".csv" )
    txt_pathname = os.path.join( self.show_dir, "txt", basename+".txt" )
    wget_pathname = os.path.join( self.show_dir, "txt", basename+".wget" )
    sh_pathname = os.path.join( self.show_dir, "txt", basename+".sh" )
    curl_pathname = os.path.join( self.show_dir, "txt", basename+"_test.sh" )
    html_pathname = os.path.join( self.show_dir, "txt", basename+".html" )
    # blip_pathname = os.path.join( self.show_dir, "txt", basename+"_blip.xml" )

    if self.options.verbose: 
        print("filenames:") 
        for n in ( json_pathname, csv_pathname, txt_pathname, 
                wget_pathname, html_pathname, ):
            print(n)

# fields to export:
    fields="id conf_key conf_url state name slug primary host_url public_url source archive_mp4_url".split()

# setup csv 
    csv = DictWriter(open(csv_pathname, "w"),fields)
    # write out field names
    csv.writerow(dict(list(zip(fields,fields))))

# setup txt
    txt=open(txt_pathname, "w")
    wget=open(wget_pathname, "w")
    sh=open(sh_pathname, "w")
    curl=open(curl_pathname, "w")
    # xml=open(blip_pathname, "w")

# setup html (not full html, just some snippits)
    html=open(html_pathname, "w")

# setup json (list written to file at end.)
    json_data=[]

    # file headers
    sh.writelines("#! /bin/bash -ex\n\n")
    curl.writelines("#! /bin/bash -ex\n\n")

    # write out episode data
    for ep in episodes:
        if not ep.rax_mp4_url: 
            # skip episodes that have not been uploaded yet.
            continue

        # fields includes output fields that are derived below
        # so fill them with None for now.
        row = dict([(f,getattr(ep,f,None)) for f in fields])
        if self.options.verbose: print(row)
        
        # blip_cli=blip_uploader.Blip_CLI()
        # blip_cli.debug = self.options.verbose

        # xml_code = blip_cli.Get_VideoMeta(ep.host_url)
        # if self.options.verbose: print xml_code
        # blip_meta = blip_cli.Parse_VideoMeta(xml_code)
        # if self.options.verbose: print blip_meta
        # if self.options.verbose: print pprint.pprint(blip_meta)

        # blip_xml=self.blip_meta(ep.host_url)
        # show_page = self.get_showpage(blip_xml)
        # row['blip'] = "%sfile/%s"%(show_page,ep.host_url)
        # row['blip'] = "http://blip.tv/file/%s"%(ep.host_url)

        # xml.write(blip_xml)
        # if self.options.verbose: print blip_xml

        # row['embed']=self.get_embed(blip_xml)
        # row['source']=self.get_media(blip_xml)

        # row['embed']=blip_meta['embed_code']
        # oggs = [i for i in blip_meta['contents'] if i['type']=='video/ogg']
        # if self.options.verbose: print pprint.pprint(oggs)
        # row['source']=oggs[0]

        row['name'] = row['name'].encode('utf-8')
        

        if self.options.verbose: print(row)
        json_data.append(row)
        csv.writerow(row)
        # txt.write("%s %s\n" % (row['blip'],row['name']))
        # html.write('<a href="%(blip)s">%(name)s</a>\n%(blip)s\n'%row)
        # wget.writelines(["%s\n" % c['url'] for c in blip_meta['contents']])
        wget.writelines( ep.rax_mp4_url + "\n" )

        sh.writelines("wget -N '%s' -O %s.mp4\n" % (
            ep.rax_mp4_url, ep.slug) )

        curl.writelines("echo Checking %s ...\n" % (
            ep.slug) )
        curl.writelines("curl -s --head  '%s' |grep -q '200 OK'\n" % (
            ep.archive_mp4_url, ) )
        curl.writelines("echo Passed.\n")

        if self.options.verbose: 
            json.dump(json_data,open(json_pathname, "w"),indent=2)
        else:
            json.dump(json_data,open(json_pathname, "w"))
        pprint.pprint(json_data)

  def add_more_options(self, parser):
        parser.add_option('-f', '--basename', 
            help='base of output filename' )

if __name__ == '__main__':
    p=csv()
    p.main()
