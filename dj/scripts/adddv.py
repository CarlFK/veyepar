#!/usr/bin/python

# Adds the .dv files to the raw files table

import  os,sys
import optparse
import datetime, time
from dateutil.parser import parse

import ocrdv
import dvdate

sys.path.insert(0, '..' )
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import settings
settings.DATABASE_NAME="../vp.db"

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

# timetweak = 3600  # seconds to adjust file timestamp to reality (like timezones)

# Raw_File.objects.filter(location__show=show).delete()

# for dt in ['2009-07-25','2009-07-26']:
def one_dir(location, dir):
    
        files=os.listdir(dir)
        seq=0
        for dv in [f for f in files if f[-3:]=='.dv']:
            seq+=1
            # print dv
            pathname = os.path.join(dir,dv)
            print pathname
            # only process new files.
            rf, created = Raw_File.objects.get_or_create(
                location=location,
                filename=dv,)

            if created: 
    
                # get file info from filesystem (start, size)
                st = os.stat(pathname)

                # get the timestamp from the dv (so from the camera)
                # start = dvdate.get_timestamp(pathname)
                # get start from filesystem create timestamp
                start=datetime.datetime.fromtimestamp( st.st_mtime ) 
                # tweak the time if the clock was wrong
                # start += datetime.timedelta(seconds=timetweak)
                # fix the filesystem create timestamp
                # ts = time.mktime(start.timetuple())

                # calc duration based on filesize
                frames = st.st_size/120000
                duration = frames/ 29.90 ## seconds

                end = start + datetime.timedelta(seconds=duration) 

                # ocr the dv - returns some text and an image

                orctext,img=ocrdv.ocrdv(pathname, frames)
                imgname = os.path.splitext(pathname)[0]+".png"
                img.save(imgname,'png')

                rf.start=start
                rf.end=end
                rf.ocrtext=orctext
                rf.save()

                # find Episodes this may be a part of, add a cutlist record
                eps = Episode.objects.filter(location=location, start__lte=end, end__gte=start)
                print eps
                for ep in eps:
                    cl, created = Cut_List.objects.get_or_create(
                        episode=ep,
                        raw_file=rf,
                        sequence=seq)


def one_loc(location,dir):
    files=os.listdir(dir)
    print files
    for dt in files:
        # dt is typicaly a date looking thint: 2009-08-20
        dir = os.path.join(dir,dt) 
        print (location,dir)
        one_dir(location,dir)

def one_show(show,dir):
    print show,dir
    for loc in Location.objects.filter(show=show):
        dir=os.path.join(dir,loc.slug)
        print show,loc,dir
        one_loc(loc, dir)

def parse_args():
    parser = optparse.OptionParser()
    parser.add_option('-s', '--show' )
    parser.add_option('-c', '--client' )
    parser.add_option('-r', '--root', default='/home/carl/Videos/veyepar' )
    parser.add_option('-l', '--list', action="store_true" )

    options, args = parser.parse_args()
    return options, args


def main():
    options, args = parse_args()

    if options.list:
        for client in Client.objects.all():
            print "\nName: %s  Slug: %s" %( client.name, client.slug )
            for show in Show.objects.filter(client=client):
                print "\tName: %s  Slug: %s" %( show.name, show.slug )
                print "\t--client %s --show %s" %( client.slug, show.slug )
    else:
        client = Client.objects.get(slug=options.client)
        show = Show.objects.get(client=client,slug=options.show)
        dir = os.path.join(options.root,client.slug,show.slug,"dv")
        print dir, client, show
        one_show(show,dir)

if __name__=='__main__': main()

