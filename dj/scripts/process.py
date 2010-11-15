#!/usr/bin/python

# abstract class for processing episodes

import optparse
import ConfigParser
import os,sys,subprocess,socket
import datetime,time

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.insert(0, '..' )
from django.conf import settings

import django
from main.models import Client, Show, Location, Episode, State, Log
from main.models import fnify

def xfnify(text):
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

  extra_options={} 

  ready_state=None
  
# defaults to ntsc stuff
  fps=29.98
  bpf=120000

  def set_dirs(self,show):
      client = show.client
      self.show_dir = os.path.join(
          self.options.media_dir,client.slug,show.slug)
      if self.options.tmp_dir:
          self.tmp_dir = self.options.tmp_dir
      else:
          self.tmp_dir = os.path.join(self.show_dir,"tmp")
      # change me to "cmd" or something beofre the next show
      self.work_dir = os.path.join(self.show_dir,"tmp")

      return


  def log_in(self,episode):
    hostname=socket.gethostname()
    what_where = "%s@%s" % (self.__class__.__name__, hostname)
    episode.locked = datetime.datetime.now()
    episode.locked_by = what_where
    try:
        state = State.objects.get(id=episode.state)
    except State.DoesNotExist:
        state = None
    self.start=datetime.datetime.now()
    self.log=Log(episode=episode,
        state=state,
        ready = datetime.datetime.now(),
        start = datetime.datetime.now(),
        result = what_where)
    self.log.save()
    episode.save()

  def log_info(self,text):
    self.log.result += text + '\n'

  def log_out(self):
    self.log.end = datetime.datetime.now()
    self.log.save()
    ep=self.log.episode
    ep.locked = None
    ep.locked_by = ''
    ep.save()
    del(self.log)
    
  def process_ep(self, episode):
    print "stubby process_ep", episode.id, episode.name
    return 

  def process_eps(self, episodes):
    for e in episodes:
      # next line requeries the db to make sure the lock field is fresh
      ep=Episode.objects.get(pk=e.id)
      if ep.locked and self.options.show_locks: 
          print "locked: ", ep
          print ep.locked, ep.locked_by
      if self.options.unlock: ep.locked=None
      if ep.locked and not self.options.force:
        if self.options.verbose:
          print '#%s: "%s" locked on %s by %s' % (ep.id, ep, ep.locked, ep.locked_by)
      else:
        # None means "don't care", 
        # ready means ready, 
        # force is dangerous and will likely mess tings up.
        if self.ready_state is None \
           or ep.state==self.ready_state \
           or self.options.force:

            self.set_dirs(ep.show)
            self.episode_dir=os.path.join( 
                self.show_dir, 'dv', ep.location.slug )

            if self.options.verbose: print ep.name
            self.log_in(ep)
            if self.process_ep(ep):
                # if the process doesn't fail,
                # and it was part of the normal process, 
                # so don't bump if the process was forced, 
                # even if it would have been had it not been forced.
                # if you force, you know better than the process,
                # so the process is going to let you bump.
                if self.ready_state is not None and not self.options.force:
                    # bump state
                    ep.state += 1
            self.end = datetime.datetime.now()
            self.log_out()
            ep.save()
        else:
            if self.options.verbose:
                print '#%s: "%s" is in state %s, ready is %s' % (
                    ep.id, ep, ep.state, self.ready_state)


  def one_show(self, show):

    self.set_dirs(show)

    locs = Location.objects.filter(show=show)
    if self.options.room:
        loc=Location.objects.get(name=self.options.room)
        locs=locs.filter(location=loc)

    for loc in locs:
        if self.options.verbose: print loc.name
        episodes = Episode.objects.filter( location=loc).order_by(
            'sequence','start',)
        if self.options.day:
            episodes=episodes.filter(start__day=self.options.day)
        # self.process_eps(episodes)
        for day in [17,18,19,20,21]:
            # self.process_eps(episodes.filter(start__day=day))
            es=episodes.filter(start__day=day)
            self.process_eps(es)

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
            episodes = episodes.filter(start__day=self.options.day)
        if self.args:
            episodes = episodes.filter(id__in=self.args)
        
        self.start=datetime.datetime.now()
        self.process_eps(episodes)
        self.end=datetime.datetime.now()
        work_time = self.end-self.start
        print "run time: %s minutes" % (work_time.seconds/60)
        # for day in [11,17,18,19,20,21]:
        #    self.process_eps(episodes.filter(start__day=day))

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
            print "client=%s\nshow=%s" %( client.slug, show.slug )
            if self.options.verbose:
                for ep in Episode.objects.filter(show=show):
                    print "\t\t id: %s state: %s %s" % ( 
                        ep.id, ep.state, ep )
    return

  def add_more_options(self, parser):
    pass
 
  def add_more_option_defaults(self, parser):
    pass
 
  def set_options(self,*bar,**extra_options):
    # hook for test runner
    self.extra_options=extra_options

  def get_options(self):
    for k,v in self.extra_options.iteritems():
      self.options.ensure_value(k,v)

  def parse_args(self):
    parser = optparse.OptionParser()

    # hardcoded defauts
    parser.set_defaults(dv_format='ntsc')
    parser.set_defaults(upload_formats="ogv")
    parser.set_defaults(media_dir=os.path.expanduser('~/Videos/veyepar'))
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


    parser.add_option('-m', '--media-dir', 
        help="media files dir", )
    parser.add_option('--tmp-dir', 
        help="temp files dir (should be local)", )
    parser.add_option('-c', '--client' )
    parser.add_option('-s', '--show' )
    parser.add_option('-d', '--day' )
    parser.add_option('-r', '--room',
              help="Location")
    parser.add_option('--dv-format', 
              help='pal, pal_wide, ntsc, ntsc_wide' )
    parser.add_option('--upload-formats', 
              help='ogg, ogv, mp4, flv, dv' )
    parser.add_option('-l', '--list', action="store_true" )
    parser.add_option('-v', '--verbose', action="store_true" )
    parser.add_option('--test', action="store_true",
              help="test mode - do not make changes to the db "
                "(not fully implemetned, for development use.")
    parser.add_option('--force', action="store_true",
              help="override ready state and lock, use with care." )
    parser.add_option('--show-locks', action="store_true",
              help="show locked status." )
    parser.add_option('--unlock', action="store_true",
              help="clear locked status, use with care." )
    parser.add_option('--whack', action="store_true",
              help="whack current episodes, use with care." )
    parser.add_option('--poll', 
              help="poll every x seconds." )

    self.add_more_options(parser)

    self.options, self.args = parser.parse_args()
    self.get_options()
    
    if self.options.verbose:
        print self.options, self.args
        from django.conf import settings
        print settings.DATABASE_ENGINE, settings.DATABASE_NAME

    if "pal" in self.options.dv_format:
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

