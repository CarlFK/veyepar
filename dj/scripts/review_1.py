#!/usr/bin/python

# review_1.py - approves all the talkes in state: review1
# hope they are good.

from process import process

from main.models import Show, Location, Episode, Raw_File, Cut_List

class review1(process):

    # this will bump everything past the review1 step
    ready_state = 6

    def process_ep(self, ep):
        if self.options.verbose: print(ep.id, ep.name)

        ret = True

        # ep.save()

        return ret

if __name__ == '__main__':
    p=review1()
    p.main()

