# rework.py - looks up a public url, 
# returns the edit page
# or if an email is passed to:
#  sets state to edit,
#  appends the email to the list of emails
#  prints some text to send 

import subprocess 
import pprint

from django.core.management.base import BaseCommand, CommandError
from django.core.urlresolvers import reverse

from main.models import Episode

class Command(BaseCommand):

        def handle(self, *args, **options):
            print args
            
            # ignore blank parameters
            if not args[0]: return

            if args[0].startswith('@'):
                urls = open(args[0][1:]).read().split('\n')
                # remove blanks
                urls = [u for u in urls if u]
                pprint.pprint(urls)
                eps = Episode.objects.filter(conf_url__in=urls)
                print len(urls), eps.count()
                for url in urls: 
                    eps = Episode.objects.filter(conf_url=url)
                    if eps: 
                        ep = eps[0]
                        url = "http://veyepar.nextdayvideo.com" + \
                            ep.get_absolute_url()
                        if ep.state:

                            if len(args)==2 \
                                    and args[1]: # empty email doesn't count
                                email = args[1]
                                ep.add_email(email)

                            edit_url = "http://veyepar.nextdayvideo.com" + \
                                reverse( "approve_episode", args= [
                                    ep.id, ep.slug, ep.edit_key ] )
                            print edit_url

                        else:

                            print ep.state, url
                            print ep.comment

                    else:
                        print "not found:", url

                return

            # look for final video url
            eps = Episode.objects.filter(public_url=args[0])

            if not eps:
                # look for just slug
                slug = args[0]
                print slug
                eps = Episode.objects.filter(
                        show__slug='fosdem_2014', slug = slug)

            if not eps:
                # look for slug
                slug = args[0].split('/')[-1][:-5]
                print slug
                eps = Episode.objects.filter(
                        show__slug='fosdem_2014', slug = slug)

            if not eps:
                # look for conf url
                # https://fosdem.org/2014/schedule/event/libguestfs/
                if args[0].startswith("https://fosdem.org/"):
                    eps = Episode.objects.filter(conf_url=args[0])

            if not eps:
                # look for room day
                # http://video.fosdem.org/2014/K4401/Sunday/
                print "guessing this is a room day.."
                x = args[0].split('/')
                year = x[3]
                location_slug = x[4]
                day = {'Saturday':1,
                        'Sunday':2 }[x[5]]
                print year, location_slug, day

                url = reverse( "episode_list", args= [
                    'fosdem',
                    'fosdem_2014',
                    ])
                print url
                qps="?client=fosdem&show=fosdem_2014&location=%s&date=%s-02-0%s" %( location_slug, year, day )
                print qps
                url = "http://veyepar.nextdayvideo.com" + \
                        url + qps
                print url
                subprocess.Popen(['firefox', url])
                url = "http://veyepar.nextdayvideo.com/main/rf_set/%s/?start_date=%s-02-0%s" % ( location_slug, year, day )
                print url
                subprocess.Popen(['firefox', url])

                return


            for ep in eps:
                print ep
                print "current state:", ep.state
                url = "http://veyepar.nextdayvideo.com" + \
                        ep.get_absolute_url()
                subprocess.Popen(['firefox', url])
                if len(args)==2 and args[1]: # empty email doesn't count
                    edit_url = reverse( "approve_episode", args= [
                            ep.id, ep.slug, ep.edit_key ] )
                    print edit_url
                    print "emails:", ep.emails
                    ep.state=1
                    if len(args) == 2:
                        email = args[1]
                    else:
                        if email[-1].lower()=="wrote:":
                            email = email[:-2]
                        email = " ".join(args[1:])
                    ep.add_email(email)
                    print email
                    print """
Here is the URL someone can use to make the fix: 
http://veyepar.nextdayvideo.com/%s
Once that happens, the system will encode, upload and send an email to:
%s

Feel free to reply with questions, we are still working out this process.
""" % (edit_url, args[1] )


