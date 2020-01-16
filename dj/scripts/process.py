#!/usr/bin/python

# abstract class for processing episodes

from pprint import pprint
import configparser
import datetime
import optparse
import os
import socket
import subprocess
import sys
import time

import fixunicode

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dj.settings")
sys.path.insert(0, '..' )
sys.path.insert(0, '../lib' )

from django.db.models import Max
from django.db import DatabaseError, connection, transaction

import django

django.setup()

from main.models import Client, Show, Location, Episode, State, Log

import swift_uploader as rax_uploader


class process():
    """
    Abstract class for processing.
    Provides basic options and itarators.
    Only operates on episodes in ready_state,
    or all if ready_state is None.
    if read_sate is not None and .processing() returns True,
        bump the episode's state:
        state=ready_state+1
    """

    extra_options = {}

    # set stop to True to stop processing at the end of episode
    # will not abort a process, like an encode, upload or anything like that.
    # it just exits these loops:
    #    for e in es: (process episodes) and do while not Done: (poll)
    stop = False

    ready_state = None

    def save_me(self, o):
        # tring to fix the db timeout problem
        try:
            o.save()
        except DatabaseError as e:
            connection.connection.close()
            connection.connection = None
            o.save()

    def run_cmd(self, cmd):
        """
        given command list
        if verbose prints stuff,
        runs it, returns pass/fail.
        """
        if self.options.verbose:
            print(cmd)
            print(' '.join(cmd))

        if self.options.test:
            print("TEST: not running command.")
            return True

        p = subprocess.Popen(cmd)
        p.wait()
        retcode = p.returncode
        if retcode:
            if self.options.verbose:
                print("command failed")
                print(retcode)
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
        sh = open(script_pathname, 'a')

        for cmd in cmds:
            if type(cmd) == list:
                print(cmd)
                log_text = ' '.join(cmd)
            else:
                log_text = cmd
                cmd = cmd.split()

            try:
                # Not sure what python v3 wants. str I guess.
                # .write(b'a') and .writeline(b'a') - Errpr must be str, not b
                sh.writelines(log_text)
                # sh.writelines([t.encode('utf-8','ignore') for t in log_text])
            except Exception as e:
                import code; code.interact(local=locals())
                import sys; sys.exit()

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

    def file2cdn(self, show, src, dst=None):
        """
        src is relitive to the show dir.
        src and dst get filled to full paths.
        Check to see if src exists,
        if it does, try to upload it to cdn
        (rax_uploader will skip if same file exists).
        """
        print("checking:", src, end='')

        if dst is None:
            dst = src

        src = os.path.join(self.show_dir, src)
        dst = os.path.join("veyepar", show.client.slug, show.slug, dst)

        if os.path.exists(src):

            u = rax_uploader.Uploader()

            u.user = show.client.rax_id

            if not show.client.bucket_id.strip():
                raise AttributeError("client.bucket_id is blank")
            u.bucket_id = show.client.bucket_id
            u.bucket = show.client.bucket_id

            u.pathname = src
            u.key_id = dst

            print(" uploading....")
            ret = u.upload()
            print(u.new_url)
            ret = u.new_url

        else:
            print(("file2cdn can't find {}".format(src)))
            ret = False

        return ret

    def set_dirs(self, show):
        client = show.client
        self.show_dir = os.path.join(
            self.options.media_dir, client.slug, show.slug)
        if self.options.tmp_dir:
            self.tmp_dir = self.options.tmp_dir
        else:
            self.tmp_dir = os.path.join(self.show_dir, "tmp")
        # change me to "cmd" or something before the next show
        self.work_dir = os.path.join(self.show_dir, "tmp")

        return

    def log_in(self, episode):
        """
        log_in/out
        create logs, and lock.unlock the episode
        """
        where = socket.gethostname()
        if os.environ.get('STY') is not None:
            where += ":" + os.environ['STY']
        what_where = "%s@%s" % (self.__class__.__name__, where)
        episode.locked = datetime.datetime.now()
        episode.locked_by = what_where[:35]
        # save the lock to disk
        episode.save()
        try:
            state = State.objects.get(sequence=episode.state)
        except State.DoesNotExist:
            state = None
        self.start = datetime.datetime.now()
        self.log = Log(
            episode=episode,
            state=state,
            ready=datetime.datetime.now(),
            start=datetime.datetime.now(),
            result=what_where)
        self.log.save()

    def log_info(self, text):
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
        print("stubby process_ep: #{} state:{} {}".format(
              episode.id, episode.state, episode.name))
        return

    def ep_in_shard(self, episode):
        """shard over ...umm.. a bunch of tmux sessions I think"""
        s = os.environ.get('STY')
        if s:
            s = s.split('-')
            if len(s) == 3:
                s = s[-1]
                if s.isdigit():
                    return episode.id % 11 == int(s)
        return True

    def ep_is_available(self, episode):
        """Is episode something we want to act on? Return boolean.

        Will take a lock on the episode.
        """
        e_id = episode.id

        if not self.ep_in_shard(episode):
            return False

        with transaction.atomic():
            # require the db to make sure the lock field is fresh
            try:
                ep = Episode.objects.select_for_update(skip_locked=True) \
                    .get(pk=e_id)
            except Episode.DoesNotExist:
                print('#%s: "%s" is locked at a DB level'
                      % (e_id, episode.name))
                return False

            # ready_state:
            # None means "don't care",
            # ready == X means ready to do X,
            # force is dangerous and will likely mess tings up.
            if self.ready_state is not None \
               and ep.state != self.ready_state \
               and not self.options.force:
                if self.options.verbose:
                    print('#%s: "%s" is in state %s, ready is %s'
                          % (e_id, ep.name, ep.state, self.ready_state))
                return False

            if self.options.unlock:
                ep.locked = None
            if ep.locked and not self.options.force:
                if self.options.verbose:
                    print('#%s: "%s" locked on %s by %s'
                          % (e_id, ep.name, ep.locked, ep.locked_by))
                return False

            if not self.options.test and not self.options.skip:
                # Don't log or lock when testing
                self.log_in(ep)

        return True

    def process_eps(self, episodes):
        # if self.options.verbose: print("process_ep: enter")

        ret = None
        for e in episodes:
            if not self.ep_is_available(e):
                continue

            # It may have been a while since whe retrieved it
            # And we've just taken a lock in a separate transaction
            e.refresh_from_db()

            self.set_dirs(e.show)
            self.episode_dir = os.path.join(
                self.show_dir, 'dv', e.location.slug)

            if self.options.verbose:
                print(e.name)

            if not self.options.quiet:
                print(self.__class__.__name__, e.id, e.name)

            if not self.options.skip:
                ret = self.process_ep(e)
                if self.options.verbose:
                    print("process_ep:", ret)

            # .process is long running (maybe, like encode or post)
            # so refresh episode in case its .stop was set
            # (would be set in some other process, like the UI)

            try:
                e_id = e.id
                e = Episode.objects.get(pk=e_id)
            except DatabaseError as err:
                connection.connection.close()
                connection.connection = None
                e = Episode.objects.get(pk=e_id)

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
                    e.state += 1
            self.end = datetime.datetime.now()
            e.save()

            if not self.options.test:
                self.log_out(e)

            if e.stop:
                if self.options.verbose:
                    print(".STOP set on the episode.")
                # send message to .process_eps which bubbles up to .poll
                self.stop = True
                # re-set the stop flag.
                e.stop = False
                e.save()
                break

            if self.options.lag:
                print("lagging....", self.options.lag)
                time.sleep(self.options.lag)

        return ret

    def one_show(self, show):
        """

        """
        self.set_dirs(show)

        locs = Location.objects.filter(show=show)
        if self.options.room:
            locs = locs.filter(slug=self.options.room)

        for loc in locs:
            if self.options.verbose:
                print(loc.name)
            # episodes = Episode.objects.filter( location=loc).order_by(
            #    'sequence','start',)
            # if self.options.day:
            #    episodes=episodes.filter(start__day=self.options.day)
            self.one_loc(show, loc)

    def work(self):
        """
        find and process episodes
        """
        # if self.options.verbose: print("work: enter")
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

        if self.ready_state is not None \
                and not self.options.force:
            episodes = episodes.filter(state=self.ready_state)

        # episodes = Episode.objects.order_by( 'sequence','start',)

        if episodes:
            self.start = datetime.datetime.now()
            ret = self.process_eps(episodes)
            self.end = datetime.datetime.now()
            work_time = self.end-self.start
            if work_time.seconds or True:
                print("run time: %s minutes" % (work_time.seconds/60))
        else:
            if self.options.poll == 0:
                print("queue empty, poll 0, exiting.")
                ret = False
            else:
                ret = True

        return ret

    def poll(self):
        done = False
        while not done:
            ret = self.work()
            if self.stop:
                done = True
            else:
                if self.options.verbose:
                    print("sleeping....")
                time.sleep(int(self.options.poll))
        return ret

    def list(self):
        """
        list clients and shows.
        """
        clients = Client.objects \
            .annotate(max_date=Max('show__episode__start')) \
            .filter(active=True) \
            .order_by('max_date') \

        if self.options.client:
            clients = clients.filter(slug=self.options.client)

        for client in clients:
            print("\nName: %s  Slug: %s" % (client.name, client.slug))
            shows = Show.objects.filter(client=client) \
                .annotate(max_date=Max('episode__start')) \
                .order_by('max_date')

            # if self.options.show:
            #    shows = shows.filter(slug=self.options.show)

            for show in shows:
                print(show)
                print("\tName: %s  Slug: %s" % (show.name, show.slug))
                print("\t--client %s --show %s" % (client.slug, show.slug))
                print("client=%s\nshow=%s" % (client.slug, show.slug))
                locations = show.locations.filter(
                        active=True).order_by('sequence')
                for loc in locations:
                    print(("room={}".format(loc.slug)))

                if self.options.verbose:
                    for ep in Episode.objects.filter(show=show):
                        print("\t\t id: %s state: %s %s"
                              % (ep.id, ep.state, ep))
        return

    def add_more_options(self, parser):
        pass

    def add_more_option_defaults(self, parser):
        pass

    def set_options(self, *bar, **extra_options):
        # hook for test runner
        self.extra_options = extra_options

    def get_options(self):
        for k, v in self.extra_options.items():
            self.options.ensure_value(k, v)
            setattr(self.options, k, v)

    def parse_args(self):
        """
        parse command line arguments.
        """
        parser = optparse.OptionParser()

        # hardcoded defaults
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

        config = configparser.RawConfigParser()
        files = config.read([
            '/etc/veyepar/veyepar.cfg',
            os.path.expanduser('~/veyepar.cfg'),
            'veyepar.cfg',
            ])

        if files:
            d = dict(config.items('global'))
            # don't want this somehow getting set in .config - too dangerous.
            d['whack'] = False
            parser.set_defaults(**d)
            if 'verbose' in d:
                print("using config file(s):", files)
                print(d)

        parser.add_option('-m', '--media-dir',
                          help="media files dir", )
        parser.add_option('--tmp-dir',
                          help="temp files dir (should be local)", )
        parser.add_option('-c', '--client')
        parser.add_option('-s', '--show')
        parser.add_option('-d', '--day')
        parser.add_option('-r', '--room',
                          help="Location")
        parser.add_option('--dv-format',
                          help='pal, pal_wide, ntsc, ntsc_wide')
        parser.add_option('--upload-formats',
                          help='ogg, ogv, mp4, flv, dv')
        parser.add_option('-l', '--list', action="store_true")
        parser.add_option('-v', '--verbose', action="store_true")
        parser.add_option('-q', '--quiet', action="store_true")
        parser.add_option(
            '--debug-log', action="store_true",
            help="append logs to .description so it gets posted to blip")
        parser.add_option(
            '--test', action="store_true",
            help="test mode - do not make changes to the db.  maybe. "
                 "(not fully implemented, for development use.")
        parser.add_option('--ready-state', type="int",
                          help="set self.ready_state")
        parser.add_option('--force', action="store_true",
                          help="override ready state and lock, use with care.")
        parser.add_option('--unlock', action="store_true",
                          help="clear locked status, use with care.")
        parser.add_option('--whack', action="store_true",
                          help="whack current episodes, use with care.")
        parser.add_option('--skip', action="store_true",
                          help="skip processing and bump state.")
        parser.add_option('--lag', type="int",
                          help="delay in seconds between processing episodes.")
        parser.add_option('--poll',
                          help="poll every x seconds.")

        self.add_more_options(parser)

        self.options, self.args = parser.parse_args()
        # strip # from #123
        self.args = [a.strip('#') for a in self.args]

        # this needs to be done better:
        self.options.upload_formats = self.options.upload_formats.split()

        self.get_options()

        if self.options.verbose:
            # import code; code.interact(local=locals())
            pprint(self.options.__dict__)
            pprint(self.args)

        if self.options.ready_state:
            self.ready_state = self.options.ready_state


        if self.options.poll and self.options.force:
            print("poll and force is a bad idea.  So no.")
            return False


        return True

    def whoami(self, iam=None):
        if iam is None:
            iam =  self.__class__.__name__
        print( '\033]2;{}\033\\'.format(iam))

        return iam


    def main(self):

        if self.parse_args():

            self.whoami()

            if self.options.list:
                ret = self.list()
            elif self.options.poll:
                ret = self.poll()
            else:
                ret = self.work()

        return ret


if __name__ == '__main__':
    p = process()
    p.main()
