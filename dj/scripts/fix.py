#!/usr/bin/python

# fix.py - mass fix some goof

from process import process

from main.models import Show, Location, Episode, Raw_File, Cut_List

class push(process):

    # this will bump everything past the review1 step
    ready_state = 6

    def process_ep(self, ep):
        if self.options.verbose: print ep.id, ep.name

        ret = True

        # ep.save()

        return ret

if __name__ == '__main__':
    p=push()
    p.main()

