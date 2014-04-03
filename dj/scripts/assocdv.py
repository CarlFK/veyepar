#!/usr/bin/python

# creates cutlist items for dv files that might belong to an episode

import os, datetime
import process
from main.models import Location, Episode, Raw_File, Cut_List, Client, Show
from main.views import mk_cuts

from django.db.models import Q

class ass_dv(process.process):

    ready_state = 1

    # hook for run_tests to hack some values into
    cuts=[]
    
    def process_ep(self, episode):

        # skip if there is already a cut list
        # if episode.cut_list_set.count():
        #    return 

        self.cuts = mk_cuts(episode)
        print "self.cuts", self.cuts

if __name__=='__main__': 
    p=ass_dv()
    p.main()

