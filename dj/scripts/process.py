#!/usr/bin/python

# abstract class for processing episodes

import optparse
import ConfigParser
import os,sys,subprocess
import datetime,time

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.insert(0, '..' )
import settings
settings.DATABASE_NAME="../vp.db"

import django
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
  if processing returns True, 
      state=ready_state+1
  """

  ready_state=1
  
# defaults to ntsc stuff
  fps=29.98
  bpf=120000

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
            location = ep.location
            show = ep.show
            client = show.client
            self.show_dir = os.path.join(
                self.options.mediadir,client.slug,show.slug)
            self.episode_dir=os.path.join( self.show_dir, 'dv', 
                ep.location.slug )
            self.log_in(ep)
            if self.process_ep(ep):
                ep.state=self.ready_state+1
            self.log_out()
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

  def work(self):
        """
        find and process episodes
        """
        episodes = Episode.objects
        if self.options.client: 
            clients = Client.objects.filter(slug=self.options.client)
            episodes = episodes.filter(show__client__in=clients)
        if self.options.show: 
            shows = Show.objects.filter(slug=self.options.show)
            episodes = episodes.filter(show__in=shows)
        if self.options.day:
            episodes = episodes.filter(start__day=options.day)
        if self.args:
            episodes = episodes.filter(id__in=self.args)

        self.process_eps(episodes)

        return

  def poll(self):
        done=False
        while not done:
            self.work()
            if self.options.verbose: print "sleeping...."
            time.sleep(int(self.options.poll))

 
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
                for ep in Episode.objects.filter(show=show):
                    print "\t\t id: %s state: %s %s" % ( 
                        ep.id, ep.state, ep )
    return

  def add_more_options(self, parser):
    pass
 
  def add_more_option_defaults(self, parser):
    pass
 
  def parse_args(self):
    parser = optparse.OptionParser()

    # hardcoded defauts
    parser.set_defaults(format='dv_ntsc')
    parser.set_defaults(upload_formats="ogv")
    parser.set_defaults(mediadir=os.path.expanduser('~/Videos/veyepar'))
    self.add_more_option_defaults(parser)

    # read from config file, overrides hardcoded
    """
    >>> open('blip_uploader.cfg').read()
    '[global]\ncategory=7\nlicense=13\ntopics=test\n'
    >>> config.read('blip_uploader.cfg')
    >>> config.items('global')
    [('category', '7'), ('topics', 'test'), ('license', '13')]
    """

    config = ConfigParser.RawConfigParser()
    files=config.read(['veyepar.cfg',
                os.path.expanduser('~/veyepar.cfg')])
    if files:
        d=dict(config.items('global'))
        d['whack']=False # don't want this somehow getting set in .conf
        parser.set_defaults(**d)
        if 'verbose' in d: 
            print "using config file(s):", files
            print d


    parser.add_option('-m', '--mediadir', 
        help="media files dir", )
    parser.add_option('-c', '--client' )
    parser.add_option('-s', '--show' )
    parser.add_option('-d', '--day' )
    parser.add_option('-r', '--room',
              help="Location")
    parser.add_option('--format', 
              help='pal, pal_wide, ntsc, ntsc_wide' )
    parser.add_option('--upload-formats', 
              help='ogg, ogv, mp4, flv, dv' )
    parser.add_option('-l', '--list', action="store_true" )
    parser.add_option('-v', '--verbose', action="store_true" )
    parser.add_option('--test', action="store_true",
              help="test mode - do not make changes to the db "
                "(not fully implemetned, for development use.")
    parser.add_option('--force', action="store_true",
              help="override ready state, use with care." )
    parser.add_option('--whack', action="store_true",
              help="whack current episodes, use with care." )
    parser.add_option('--poll', 
              help="poll every x seconds." )

    self.add_more_options(parser)

    self.options, self.args = parser.parse_args()
    
    if self.options.verbose:
        print self.options, self.args
        from django.conf import settings
        print settings.DATABASE_ENGINE, settings.DATABASE_NAME

    if "pal" in self.options.format.lower():
        self.fps=25.0
        self.bpf=144000 

    return 

  def main(self):
    self.parse_args()

    if self.options.list:
        self.list()
    elif self.options.poll:
        self.poll()
    else:
    	self.work()

if __name__ == '__main__':
    p=process()
    p.main()

