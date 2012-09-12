#!/usr/bin/python

# mk_public.py - flip state on hosts from private to public
# private = not listed, can be seen if you know the url
#     the presenters have been emaild the URL, 
#     they are encouraged to advertise it.
# public = advertised, it is ready for the world to view.  
#     It will be tweeted at @NextDayVideo

"""
Currently none of the pirvate states have been implemented.
See TODO.txt for details
"""

from process import process

from main.models import Show, Location, Episode, Raw_File, Cut_List

class push(process):

    # this will bump everything past the review1 step
    ready_state = 9

    def process_ep(self, ep):
        if self.options.verbose: print ep.id, ep.name

        # set youtube to public
        # set pyvideo state to live

        ret = True

        # ep.save()

        return ret

if __name__ == '__main__':
    p=push()
    p.main()

