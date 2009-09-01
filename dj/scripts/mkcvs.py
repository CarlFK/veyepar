#!/usr/bin/python

# exports a cvs file of all epsides in a show

import optparse
import  os,sys
from csv import DictWriter

sys.path.insert(0, '..' )
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import settings
print settings.DATABASE_NAME
settings.DATABASE_NAME="../vp.db"

from main.models import Client, Show, Location, Episode

def exp_show(show, filename):
    """ Export all the episodes of a show. """
    
    fields="id state name primary comment".split()

    writer = DictWriter(open(filename, "w"),fields, extrasaction='ignore')
    # write out field names
    writer.writerow(dict(zip(fields,fields)))

    # write out episode data
    for ep in Episode.objects.filter(location__show=show).order_by('state'):
        writer.writerow(ep.__dict__)

def parse_args():
    parser = optparse.OptionParser()
    parser.add_option('-f', '--file' )
    parser.add_option('-s', '--show' )
    parser.add_option('-c', '--client' )
    parser.add_option('-l', '--list', action="store_true" )

    options, args = parser.parse_args()
    return options, args

def main(options, args):

    if options.list:
        for client in Client.objects.all(): 
            print "\nName: %s  Slug: %s" %( client.name, client.slug )
            for show in Show.objects.filter(client=client):
                print "\tName: %s  Slug: %s" %( show.name, show.slug )
                print "\t--client %s --show %s" %( client.slug, show.slug )
    else:    
        client = Client.objects.get(slug=options.client)
        show = Show.objects.get(client=client,slug=options.show)
        filename = "%s.csv" % (optins.file if options.file 
            else "%s_%s" % (client.slug,show.slug))
        print client, show, filename
        exp_show( show, filename )


if __name__ == '__main__':
    main(parse_args())

