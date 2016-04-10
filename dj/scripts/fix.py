#!/usr/bin/python

# fix.py - mass fix some goof

from process import process

from main.models import Show, Location, Episode, Raw_File, Cut_List

class fix(process):

    # this will bump everything from 5 back to 4
    ready_state = 7

    def process_ep(self, ep):
        if self.options.verbose: print(ep.id, ep.name)

        ep.state = 4
        ep.save()

        ret = False # False else it will bump it +1)

        return ret

if __name__ == '__main__':
    p=fix()
    p.main()

