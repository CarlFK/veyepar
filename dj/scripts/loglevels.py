#!/usr/bin/python

# loglevels.py
# logs the average level of the first .dv file
# (appends it to comments, cuz I don't have a better place)

import os
import gslevels

from process import process

class cklev(process):

    ready_state = 3

    def process_ep(self, ep):
        print ep.id, ep.name
        cls = ep.cut_list_set.all()
        if cls:
            rf=cls[0].raw_file.filename
            rawpathname = os.path.join(self.episode_dir,rf)
            print rawpathname

        levs = gslevels.cklev(rawpathname, 5*60, 500)
        powers=levs[0]
        if powers[0]>powers[1]:
            x='01'
        else:
            x='10'
        print x,levs
        
        ep.comment = "\n".join([x,levs.__str__(), ep.comment])

        return False ## don't bump state

if __name__ == '__main__':
    p=cklev()
    p.main()

