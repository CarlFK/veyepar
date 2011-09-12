#!/usr/bin/python

# creates svg titles for all the episodes
# used to preview the title slides, 
# enc.py will re-run the same code.

import os

from enc import enc

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

class mk_title(enc):

    ready_state = None

    def process_ep(self, episode):
        # make a title slide
        svg_name = episode.show.client.title_svg \
                if episode.show.client.title_svg \
                else "title.svg"

        template = os.path.join(self.show_dir, "bling", svg_name)
        title_base = os.path.join(self.show_dir, "titles", episode.slug)
        title_img=self.mk_title_png(template, title_base, episode)

        return False

if __name__ == '__main__':
    p=mk_title()
    p.main()

