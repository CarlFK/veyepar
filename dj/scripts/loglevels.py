#!/usr/bin/python

# loglevels.py
# logs the average level of the first .dv file
# (appends it to comments, cuz I don't have a better place)

from process import process

import gslevels


class cklev(process):

    ready_state = 3


    def process_ep(self, ep):
        print ep.id, ep.name
        print ep.cut_list.objects.all()

        filename = ''
        # levs = gslevels.cklev(file_name,5*60,500)
        # ep.comment = levs.tolist().__str__() + '\n' + ep.comment

        return False ## don't bump state

if __name__ == '__main__':
    p=cklev()
    p.main()

