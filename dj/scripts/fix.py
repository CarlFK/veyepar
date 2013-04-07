#!/usr/bin/python

# fix.py - mass fix some goof

from process import process

from main.models import Show, Location, Episode, Raw_File, Cut_List

class fix(process):

    # this will bump everything from 6 to 6+1
    ready_state = 6

    def process_ep(self, ep):
        if self.options.verbose: print ep.id, ep.name

        ret = True

        # ep.save()

        return ret

if __name__ == '__main__':
    p=fix()
    p.main()

