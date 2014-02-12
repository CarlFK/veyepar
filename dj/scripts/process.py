#!/usr/bin/python

# abstract class for processing episodes

import optparse
import ConfigParser
import os,sys,subprocess,socket
import datetime,time

import fixunicode

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dj.settings")
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
  or all if ready_state is None.
  if read_sate is not None and .processing() returns True, 
      bump the episode's state:
      state=ready_state+1
  """

  extra_options={} 

  # set stop to True to stop processing at the end of episode
  # will not abort a process, like an encode, upload or anything like that.
  # it just exits these loops: 
  #    for e in es: (process episodes) and do while not Done: (poll)
  stop = False 

  ready_state=None

# defaults to ntsc stuff
  # fps=29.98
  fps=30000/1001.0
  bpf=120000

  def run_cmd(self,cmd):
    """
    given command list
    if verbose prints stuff,
    runs it, returns pass/fail.
    """
    if self.options.verbose:
        print cmd
        print ' '.join(cmd)

    if self.options.test:
        print "TEST: not running command."
        return True

    p=subprocess.Popen(cmd)
    p.wait()
    retcode=p.returncode
    if retcode:
        if self.options.verbose:
            print "command failed"
            print retcode
        ret = False
    else:
        ret = True
    return ret

  def run_cmds(self, episode, cmds):
      """
      given a list of commands
      append them to the episode's shell script
      then run each
      abort and return False if any fail.
      """

      script_pathname = os.path.join(self.work_dir, episode.slug+".sh")
      sh = open(script_pathname,'a')

      for cmd in cmds: 
          if type(cmd)==list:
              print cmd
              log_text = ' '.join(cmd)
          else:
              log_text = cmd
              cmd=cmd.split()
          sh.writelines([t.encode('utf-8','ignore') for t in log_text])
          # sh.writelines(log_text)
          # if isinstance(s, unicode): return s.encode('utf-8') else: return s
          sh.write('\n')
          # self.log_info(log_text)
          if self.options.debug_log:
              episode.description += "\n{0:>s}\n".format(log_text, )
              episode.save()

          if not self.run_cmd(cmd):
              return False

      sh.write('\n')
      sh.close()

      return True

  def set_dirs(self,show):
      client = show.client
      self.show_dir = os.path.join(
          self.options.media_dir,client.slug,show.slug)
      if self.options.tmp_dir:
          self.tmp_dir = self.options.tmp_dir
      else:
          self.tmp_dir = os.path.join(self.show_dir,"tmp")
      # change me to "cmd" or something before the next show
      self.work_dir = os.path.join(self.show_dir,"tmp")

      return


  def log_in(self,episode):
    """
    log_in/out
    create logs, and lock.unlock the episode
    """
    where=socket.gethostname()
    if os.environ.get('STY') is not None:
        where += ":" + os.environ['STY']
    what_where = "%s@%s" % (self.__class__.__name__, where)
    episode.locked = datetime.datetime.now()
    episode.locked_by = what_where
    # save the lock to disk
    episode.save()
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

  def log_info(self,text):
    self.log.result += text + '\n'

  def log_out(self, episode):

    # done processing
    # log the end time
    # unlock the episode

    self.log.end = datetime.datetime.now()
    self.log.save()

    episode.locked = None
    episode.locked_by = ''
    episode.save()

  def process_ep(self, episode):
    print "stubby process_ep", episode.id, episode.name
    return 

  def process_eps(self, episodes):
    ret = None 
    sleepytime=False
    for e in episodes:
      # next line requires the db to make sure the lock field is fresh
      ep=Episode.objects.get(pk=e.id)
      if self.options.unlock: ep.locked=None
      if ep.locked and not self.options.force:
        if self.options.verbose:
          print '#%s: "%s" locked on %s by %s' % (ep.id, ep.name, ep.locked, ep.locked_by)
          ret = None
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
     
            if self.options.lag:
                if sleepytime: 
                    # don't lag on the first one that needs processing,
                    # we only want to lag between the fence posts.
                    print "lagging....", self.options.lag
                    time.sleep(self.options.lag)
                else:
                     sleepytime = True

            self.log_in(ep)

            if not self.options.quiet: print self.__class__.__name__, ep.id, ep.name
            if self.options.skip:
                ret = True
            else:
                ret = self.process_ep(ep)
            if self.options.verbose: print "process_ep:", ret

            # .process is long running (maybe, like encode or post) 
            # so refresh episode in case its .stop was set 
            # (would be set in some other process, like the UI)
            ep=Episode.objects.get(pk=e.id)

            if ret:
                # if the process doesn't fail,
                # and it was part of the normal process, 
                # don't bump if the process was forced, 
                # even if it would have been had it not been forced.
                # if you force, you know better than the process,
                # so the process is going to let you bump.
                # huh?!  
                # so..  ummm... 
                # 1. you can't bump None
                # 2. don't bump when in test mode
                # 3. if it wasn't forced:, bump.
                if self.ready_state is not None \
                        and not self.options.test \
                        and not self.options.force:
                    # bump state
                    ep.state += 1
            self.end = datetime.datetime.now()
            ep.save()
            self.log_out(ep)
            if ep.stop: 
                if self.options.verbose: print ".STOP set on the episode."
                # send message to .process_eps which bubbles up to .poll 
                self.stop = True
                # re-set the stop flag.
                ep.stop = False
                ep.save()
                break

        else:
            if self.options.verbose:
                print '#%s: "%s" is in state %s, ready is %s' % (
                    ep.id, ep.name, ep.state, self.ready_state)

    return ret


  def one_show(self, show):

    """
 
    """
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
        if self.options.room:
            episodes = episodes.filter(location__slug=self.options.room)
        if self.args:
            episodes = episodes.filter(id__in=self.args)

        self.start=datetime.datetime.now()
        ret = self.process_eps(episodes)
        self.end=datetime.datetime.now()
        work_time = self.end-self.start
        if work_time.seconds or True:
            print "run time: %s minutes" % (work_time.seconds/60)

        return ret

  def poll(self):
        done=False
        while not done:
            ret = self.work()
            if self.stop:
                done=True
            else: 
                if self.options.verbose: print "sleeping...."
                time.sleep(int(self.options.poll))
        return ret


  def list(self):
    """
    list clients and shows.
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
      setattr(self.options, k, v)

  def parse_args(self):
    """
    parse command line arguments.
    """
    parser = optparse.OptionParser()

    # hardcoded defaults
    parser.set_defaults(dv_format="ntsc")
    parser.set_defaults(upload_formats="mp4")
    parser.set_defaults(media_dir=os.path.expanduser('~/Videos/veyepar'))
    parser.set_defaults(lag=0)
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
        d['whack']=False # don't want this somehow getting set in .config - too dangerous.
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
    parser.add_option('-q', '--quiet', action="store_true" )
    parser.add_option('--debug-log', action="store_true",
              help="append logs to .description so it gets posted to blip" )
    parser.add_option('--test', action="store_true",
              help="test mode - do not make changes to the db.  maybe. "
                "(not fully implemented, for development use.")
    parser.add_option('--ready-state', type="int",
              help="set self.ready_state" )
    parser.add_option('--force', action="store_true",
              help="override ready state and lock, use with care." )
    parser.add_option('--unlock', action="store_true",
              help="clear locked status, use with care." )
    parser.add_option('--whack', action="store_true",
              help="whack current episodes, use with care." )
    parser.add_option('--skip', action="store_true",
              help="skip processing and bump state." )
    parser.add_option('--lag', type="int",
        help="delay in seconds between processing episodes.")
    parser.add_option('--poll',
              help="poll every x seconds." )

    self.add_more_options(parser)

    self.options, self.args = parser.parse_args()
    # this needs to be done better:
    self.options.upload_formats = self.options.upload_formats.split()
    self.get_options()

    if self.options.verbose:
        print self.options, self.args

    if "pal" in self.options.dv_format:
        self.fps=25.0
        self.bpf=144000 

    if self.options.ready_state:
        self.ready_state = self.options.ready_state

    return 



  def main(self):
    self.parse_args()

    if self.options.list:
        ret = self.list()
    elif self.options.poll:
        ret = self.poll()
    else:
        ret = self.work()

    return ret

if __name__ == '__main__':
    p=process()
    p.main()

