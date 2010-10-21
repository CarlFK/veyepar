#!/usr/bin/python

# creates cutlist items for dv files passed on the command line

import os,sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.insert(0, '..' )

from main.models import Episode, Raw_File, Cut_List

ep = Episode.objects.get(id=2)

date_dir='2010-10-10'

file_names="""08:52:47.dv
08:59:44.dv
09:06:08.dv
10:16:11.dv
10:33:29.dv
11:09:37.dv
11:10:05.dv
11:12:40.dv
12:16:51.dv"""

file_names="2010-10-10/sacwedding/sacwedding003.dv"
file_names="sacwedding/sacwedding003.dv"

seq=0
for fn in file_names.split('\n'): 
    pn= date_dir+'/'+fn 
    print pn, 
    dv = Raw_File.objects.get(filename = pn)
    seq+=1

    cl, created = Cut_List.objects.get_or_create(
        episode=ep,
        raw_file=dv )
    if created:
        cl.sequence=seq
        cl.save()

