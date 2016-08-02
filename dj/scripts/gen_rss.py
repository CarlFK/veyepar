#!/usr/bin/python

# create an rss feed file. 
# needs to get the file size from the file system, 
# so needs to be run on a box with fiile system access to the files

import os, subprocess, sys
from process import process

import datetime
import PyRSS2Gen

import django
from main.models import Show, Location, Episode

class gen_rss(process):

    items = []                 

    def process_ep(self,ep):

      for ext in self.options.upload_formats:

        fullpathname = os.path.join(
            self.show_dir, ext, ep.slug + "." + ext )

        if os.path.exists( fullpathname ):

            # this should be ep.some_url but oh well.
            url = '%s/%s/%s/%s.%s' % (self.options.base_url,
                    ep.start.year, ep.show.slug, ep.slug, ext)

            info = PyRSS2Gen.RSSItem(
                title = ep.name,
                description = ep.description,
                guid = PyRSS2Gen.Guid(ep.conf_url),
                pubDate = ep.start,
                link = ep.conf_url,
                enclosure = PyRSS2Gen.Enclosure(
                    url = url,
                    length = os.stat( fullpathname ).st_size,
                    type = 'video/'+ext,
                    )
            )

            self.items.append(info)

                          
    def process_eps(self, eps):

        super(gen_rss, self).process_eps(eps)

        show = eps[0].show

        fh = open('rss2.xml', 'w')

        rss = PyRSS2Gen.RSS2( 
            title = "{} video RSS feed".format(show.name),
            link = show.conf_url,
            description = "The published videos from {}".format(
                show.name),
            lastBuildDate = datetime.datetime.now(),
            items = self.items)

        rss.write_xml(fh, encoding = 'UTF-8')

        fh.close()

        return 

    def add_more_options(self, parser):
        parser.add_option('--base-url', 
          default='http://meetings-archive.debian.net/pub/debian-meetings',
          help="URL where the media is stored.")


if __name__=='__main__':
    p=gen_rss()
    p.main()

