#!/usr/bin/python

# get_vimeo.py - pulls descriptions from vimeo
# used when descriptions are added by hand to vimeo
# and we want to get them into pyvideo.org

from steve.util import scrapevideo, html_to_markdown
from process import process

from main.models import Episode

class Get_vimeo(process):

    # this will bump everything past the review1 step
    ready_state = None

    def process_ep(self, ep):
        if self.options.verbose: print ep.id, ep.name

        meta = scrapevideo(ep.host_url)

        # print ep.host_url
        # print meta['description'] 
        description = html_to_markdown(meta['description'])
        ep.description = description 

        title = html_to_markdown(meta['title'])
        if ep.name <> title:
            print ep.host_url
            print "veyepar:\t%s" %( ep.name, )
            print "  vimeo:\t%s" %( title, )
            print


        ep.save()
        ret = None
        return ret

    def add_more_options(self, parser):
        parser.add_option('-u', '--update', action="store_true", 
          help='update when diff, else print' )


if __name__ == '__main__':
    p=Get_vimeo()
    p.main()

