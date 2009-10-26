#!/usr/bin/python

# abstract class for processing episodes

import optparse
import os,sys,subprocess
import datetime

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.insert(0, '..' )
import settings
settings.DATABASE_NAME="../vp.db"

from main.models import Client, Show, Location, Episode, State, Log

def fnify(text):
    """
    file_name_ify - make a file name out of text, like a talk title.
    convert spaces to _, remove junk like # and quotes.
    like slugify, but more file name friendly.
    """
    fn = text.replace(' ','_')
    fn = ''.join([c for c in fn if c.isalpha() or c.isdigit() or (c in '_') ])
    return fn

class process(object):
  """
  Abstract class for processing.
  Provides basic options and itarators.
  Only operates on episodes in ready_state,
  promotes them to done_state.
  """

  ready_state=2

  def log_in(self,episode):
    state,create = State.objects.get_or_create(id=1)
    self.log=Log(episode=episode,
        state=state,
        ready = datetime.datetime.now(),
        start = datetime.datetime.now())
    self.log.save()

  def log_info(self,text):
    print text
    self.log.result += text + '\n'

  def log_out(self):
    self.log.end = datetime.datetime.now()
    self.log.save()
    del(self.log)
    
  def process_ep(self, episode):
    print episode.id, episode.name
    return 

  def process_eps(self, episodes):
    for ep in episodes:
        if ep.state==self.ready_state or self.options.force:
            self.episode_dir=os.path.join( self.show_dir, 'dv', 
                ep.location.slug )
            self.log_in(ep)
            if self.process_ep(ep):
                self.log_out()
                ep.state=self.done_state
                ep.save()
        else:
            if self.options.verbose:
                print '#%s: "%s" is in state %s, ready is %s' % (
                    ep.id, ep, ep.state, self.ready_state)


  def one_show(self, show):
    locs = Location.objects.filter(show=show)
    if self.options.room:
        loc=Location.objects.get(name=self.options.room)
        locs=locs.filter(location=loc)
    # for loc in Location.objects.filter(show=show):
    for loc in locs:
        if self.options.verbose: print loc.name
        episodes = Episode.objects.filter(
            location=loc).order_by('sequence','start',)
        #    location=loc,state=self.ready_state).order_by('start','location')
        if self.options.day:
            episodes=episodes.filter(start__day=self.options.day)
        self.process_eps(episodes)

  def add_more_options(self, parser):
    pass
 
  def list(self):
    """
    list clients and shows.
    todo: filter on something.
    """
    for client in Client.objects.all():
        print "\nName: %s  Slug: %s" %( client.name, client.slug )
        for show in Show.objects.filter(client=client):
            print "\tName: %s  Slug: %s" %( show.name, show.slug )
            print "\t--client %s --show %s" %( client.slug, show.slug )
            if self.options.verbose:
                for ep in Episode.objects.filter(location__show=show):
                    print "\t\t id: %s state: %s %s" % ( 
                        ep.id, ep.state, ep )
    return

  def parse_args(self):
    parser = optparse.OptionParser()
    parser.add_option('-m', '--mediadir', help="media files dir",
        default= '/mnt/nfs/dhcp123/video/veyepar' )
        # default= '/home/carl/Videos/veyepar' )
        # default= '/media/pycon25wed/Videos/veyepar' )
# need to figure out how to do a local config file.
    parser.add_option('-c', '--client' )
    parser.add_option('-s', '--show' )
    parser.add_option('-d', '--day' )
    parser.add_option('-r', '--room',
              help="Location")
    parser.add_option('-l', '--list', action="store_true" )
    parser.add_option('-v', '--verbose', action="store_true" )
    parser.add_option('--test', action="store_true",
              help="test mode - do not make changes to the db (not fully implemetned, for development use.")
    parser.add_option('--force', action="store_true",
              help="overfide ready state, use with care." )
    parser.add_option('--whack', action="store_true",
              help="whack current episodes, use with care." )

    self.add_more_options(parser)

    options, args = parser.parse_args()
    self.options = options

    return options, args

  def main(self):
    options, args = self.parse_args()

    if options.list:
        self.list()
    elif options.client and options.show:
        client = Client.objects.get(slug=options.client)
        show = Show.objects.get(client=client,slug=options.show)
        self.show_dir = os.path.join(self.options.mediadir,client.slug,show.slug)
        self.one_show(show)

    elif options.day:
        show = Show.objects.get(name='PyOhio09')
        episodes = Episode.objects.filter(location__show=show,start__day=options.day)
        enc_eps(episodes)
    else:
        episodes = Episode.objects.filter(id__in=args)
        print episodes
        show = episodes[0].location.show
        client = show.client
        self.show_dir = os.path.join(self.options.mediadir,client.slug,show.slug)
        self.process_eps(episodes)
    

if __name__ == '__main__':
    p=process()
    p.main()

