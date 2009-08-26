#!/usr/bin/python

# posts to blip.tv, tweets it

from blip_uploader import Upload

import tweeter
import optparse
import re
import os,sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.insert(0, '..' )
import settings
settings.DATABASE_NAME="../vp.db"

from main.models import Show, Location, Episode, Raw_File, Cut_List

def do_one(ep):
    print ep.id, ep.name
    loc = ep.location
    show = loc.show
    client = show.client

    # look for a thumb
    root='/home/carl/Videos' 
    root="%s/%s/%s" % (root,client.slug,show.slug)
    dt=ep.start.strftime("%Y-%m-%d")
    dir="%s/dv/%s/%s" % (root,dt,loc.slug)

    for cut in Cut_List.objects.filter(episode=ep).order_by('sequence'):
        basename = cut.raw_file.basename()        
        thumb="%s/%s.jpg"%(dir,basename)
        if os.path.exists(thumb): break
    
    oggpathname = "%s/%s.ogg"%(show.slug,ep.slug)
    description = "%s</br>/n</br>/n%s" % (ep.description, show.description)

    meta = {
        'title': ep.name,
        'description': description,
        "topics": "%s, %s, python, pycon, conference, ohio, 2009"%(show.name,show.client.name),
        "license": "13",
        "categories_id": "10",
        }

    print oggpathname, thumb

    # username,pwd = "carlfk","goat"
    username,pwd = "pyohio09","py0hio"
    # response = Upload("", username, pwd, oggpathname, meta, thumb)
    # responsexml = response.read()
    # blipurl = re.search("post_url>(.*)</post" ,responsexml).groups()[0]
    blipurl = "http://blip.tv/file/2517969"
    if blipurl:
        print blipurl
        prefix = "#%s VIDEO -" % show.client.name
        tweet = tweeter.notify(prefix, ep.name, blipurl)
        tweetid=re.search("<id>(.*)</id>" ,tweet).groups()[0]
        tweeturl="http://twitter.com/cfkarsten/status/%s"%(tweetid,)
        print tweeturl
        ep.state = 4
        ep.comment += blipurl
    else:
        ep.comment += "upload failed\n"
    ep.save()

def do_eps(episodes):
    for ep in episodes:
        if ep.state==3:
             # print ep.id, ep.name
             do_one(ep)

def do_show(show):
    locs = Location.objects.filter(show=show)
    for loc in locs:
        episodes = Episode.objects.filter(location=loc,state=2)
        do_eps(episodes)


def parse_args():
    parser = optparse.OptionParser()
    parser.add_option('-a', '--all' )
    parser.add_option('-s', '--show' )
    parser.add_option('-d', '--day' )

    options, args = parser.parse_args()
    return options, args


def main():
    options, args = parse_args()

    if options.all:
        show = Show.objects.get(name='PyOhio09')
        do_show(show)
    elif options.show:
        show = Show.objects.get(name=options.show)
        d0_show(show)
    elif options.day:
        show = Show.objects.get(name='PyOhio09')
        episodes = Episode.objects.filter(location__show=show,start__day=options.day)
        do_eps(episodes)
    else:
        episodes = Episode.objects.filter(id__in=args)
        do_eps(episodes)

    

if __name__ == '__main__':
    main()

