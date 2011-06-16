#!/usr/bin/python

# creates cutlist items for dv files that might belong to an episode

import os, datetime
import process
from main.models import Location, Episode, Raw_File, Cut_List, Client, Show
from main.views import mk_cuts

from django.db.models import Q

class ass_dv(process.process):

    # hook for run_tests to hack some values into
    cuts=[]
    
    def process_ep(self, episode):
        self.cuts = mk_cuts(episode)

if __name__=='__main__': 
    p=ass_dv()
    p.main()

