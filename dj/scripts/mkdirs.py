#!/usr/bin/python

# Makes the dir tree to put files into

import  os,sys
import optparse

sys.path.insert(0, '..' )
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import settings
settings.DATABASE_NAME="../vp.db"

from main.models import Client, Show, Location

def mkdirs(root,client,show):
    root = "%s/%s/%s" % (root, client.slug, show.slug)
    print "%s/dv" % (root,)
    os.makedirs("%s/dv" % (root,))
    locs = Location.objects.filter(show=show)
    for loc in locs:
         dir="%s/dv/%s" % (root,loc.slug)
         print dir
         os.mkdir(dir)

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
        root = options.root
        print root, client, show
        mkdirs( root, client, show )

if __name__=='__main__': main()
