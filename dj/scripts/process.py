#!/usr/bin/python

# abstract class for processing episodes

import optparse
import os,sys,subprocess
import datetime

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.insert(0, '..' )
import settings
settings.DATABASE_NAME="../vp.db"

from main.models import Client, Show, Location, Episode 

class process(object):
  """
  Abstract class for processing.
  Provides basic options and itarators.
  Only operates on episodes in ready_state,
  promotes them to done_state.
  """

  def process_ep(self, episode):
    print episode.id, episode.name
    return 

  def process_eps(self, episodes):
    for ep in episodes:
        if ep.state==self.ready_state:
            self.episode_dir=os.path.join( self.show_dir, 'dv', 
                ep.location.slug )
            if self.process_ep(ep):
                ep.state=self.done_state
                ep.save()

  def one_show(self, show):
    locs = Location.objects.filter(show=show)
    for loc in locs:
        episodes = Episode.objects.filter(location=loc,state=self.ready_state)
        self.process_eps(episodes)

  def add_more_options(self, parser):
    pass
 
  def parse_args(self):
    parser = optparse.OptionParser()
    parser.add_option('-r', '--rootdir', help="media files dir",
        default= '/media/pycon25wed/Videos/veyepar' )
    parser.add_option('-c', '--client' )
    parser.add_option('-s', '--show' )
    parser.add_option('-d', '--day' )
    parser.add_option('-l', '--list', action="store_true" )
    parser.add_option('-v', '--verbose', action="store_true" )
    parser.add_option('--whack', action="store_true",
              help="whack current episodes, use with care." )

    self.add_more_options(parser)

    options, args = parser.parse_args()
    self.options = options

    return options, args

  def main(self):
    options, args = self.parse_args()

    if options.list:
        for client in Client.objects.all():
            print "\nName: %s  Slug: %s" %( client.name, client.slug )
            for show in Show.objects.filter(client=client):
                print "\tName: %s  Slug: %s" %( show.name, show.slug )
                print "\t--client %s --show %s" %( client.slug, show.slug )
                for ep in Episode.objects.filter(location__show=show):
                    print "\t\t id: %s state: %s %s" % ( 
                        ep.id, ep.state, ep.name )
    elif options.client and options.show:
        client = Client.objects.get(slug=options.client)
        show = Show.objects.get(client=client,slug=options.show)
        self.show_dir = os.path.join(self.options.rootdir,client.slug,show.slug)
        self.one_show(show)

    elif options.day:
        show = Show.objects.get(name='PyOhio09')
        episodes = Episode.objects.filter(location__show=show,start__day=options.day)
        enc_eps(episodes)
    else:
        episodes = Episode.objects.filter(id__in=args)
        print episodes
        self.process_eps(episodes)
    

if __name__ == '__main__':
    p=process()
    p.main()

