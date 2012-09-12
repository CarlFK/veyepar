#!/usr/bin/python

# review_2.py - 
# once it has been reviewed
# bumps state from review_2 to next state (mk_public)
#   same as using the web UI to bump the state 


from process import process

from main.models import Show, Location, Episode, Raw_File, Cut_List

class push(process):

    # this will bump everything past the review1 step
    ready_state = 8

    def process_ep(self, ep):
        if self.options.verbose: print ep.id, ep.name

        # there really is nothing to do here.
        # process.py takes care of bumping the state.

        ret = True

        # ep.save()

        return ret

if __name__ == '__main__':
    p=push()
    p.main()

