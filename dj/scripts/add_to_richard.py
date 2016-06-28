#!/usr/bin/python

# push metadata to richard (like pyvideo.org)

import datetime
import pprint
from urllib.parse import urlparse, parse_qs
from process import process as Process

from steve.richardapi import \
        create_video, get_video, update_video, \
        STATE_DRAFT, STATE_LIVE, \
        MissingRequiredData

from steve.restapi import Http4xxException

from steve.util import scrapevideo

import requests

from django.template.defaultfilters import linebreaks, urlize, force_escape
from django.conf import settings

from main.models import Show, Location, Episode

import pw

def get_video_id(url):
    v_id = url.split('/video/')[1].split('/')[0]
    return v_id

class add_to_richard(Process):

    ready_state = 5

    def process_ep(self, ep):
        """ adds Episode to richard

        :arg ep: Episode to add to richard
        :returns: different things based on what is happening
                  a video dictionary for updated videos
                  a richard url for newly added videos
                  False if there was an exception during processing

        """
        # richard categories are stored in Client and Show
        # ChiPy is an example of something that uses Client,
        # pycon 2014 and 300SoC are in Show.
        self.category_key = ep.show.category_key \
                or ep.show.client.category_key

        richard_id = self.options.richard_id or ep.show.client.richard_id
        self.host = pw.richard[richard_id]

        self.richard_endpoint = \
            'http://{hostname}/api/v2'.format(hostname=self.host['host'])
        # self.api = API(self.richard_endpoint)

        """
        if self.options.verbose: 
            print "Auth creds:"
            print self.richard_endpoint, \
                    self.host['user'], self.host['api_key'], \
                    {'category_key': self.category_key}
        """

        
        """
        # FIX richard: need API for adding new categories.
        # FIXME using chatty hack due to problems with category handling
        if not self.options.test:
            create_category_if_missing( self.richard_endpoint, 
                    self.host['user'], self.host['api_key'], 
                    {'title': self.category_key,
                        'description':ep.show.description})
        """
        
        video_data = self.create_richard_episode_dict(ep, state=2)
        # perhaps we could just update the dict based on scraped_meta
        # scraped_metadata = self.get_scrapevideo_metadata(ep.host_url)
        # video_data['thumbnail_url'] = scraped_metadata.get('thumbnail_url','')

        # if self.options.title_thumb:
        if 'thumbnail_url' not in video_data:
            # half baked idea:
            # use title slide as place holder image until video is produced.
            cdn = "http://veyepar.{}.cdn.nextdayvideo.com/veyepar".format(
                    ep.show.client.bucket_id)
            video_data['thumbnail_url'] = "%s/%s/%s/titles/%s.png" % ( 
                    cdn, ep.show.client.slug, ep.show.slug, ep.slug )
        if ep.host_url is None:
            pass

        elif "youtube" in ep.host_url or "youtu.be" in ep.host_url:  
            scraped_metadata = self.get_scrapevideo_metadata(ep.host_url)
            if "youtu.be" in ep.host_url:  
                # for some reason this does not give object_embed_code
                # so fix it with a hammer.
                # ep.host_url = scraped_metadata['link'] 
                scraped_metadata = self.get_scrapevideo_metadata(ep.host_url)
            
            video_data['thumbnail_url'] = scraped_metadata.get('thumbnail_url','')
            video_data['embed'] = \
                    scraped_metadata.get('object_embed_code','')

        elif "vimeo" in ep.host_url:  
            # video_data['embed'] = scraped_metadata.get('embed_code','')
            params = {'vimeo_id': ep.host_url.split('/')[-1]}
            video_data['embed'] ="""<object width="640" height="480"><param name="allowfullscreen" value="true"><param name="allowscriptaccess" value="always"><param name="movie" value="http://vimeo.com/moogaloop.swf?show_byline=1&amp;fullscreen=1&amp;clip_id=%(vimeo_id)s&amp;color=&amp;server=vimeo.com&amp;show_title=1&amp;show_portrait=0"><embed src="http://vimeo.com/moogaloop.swf?show_byline=1&amp;fullscreen=1&amp;clip_id=%(vimeo_id)s&amp;color=&amp;server=vimeo.com&amp;show_title=1&amp;show_portrait=0" allowscriptaccess="always" height="480" width="640" allowfullscreen="true" type="application/x-shockwave-flash"></embed></object>""" % params 

        if self.options.verbose: 
            print("1. video_data:")
            pprint.pprint(video_data)

        if \
            not video_data['video_mp4_url'] \
            or not video_data['source_url'] \
            or not video_data['embed']:
                import code
                # code.interact(local=locals())


        if self.is_already_in_richard(ep):
            # get richard ID
            v_id = get_video_id( ep.public_url)
            ret = self.update_richard( v_id, video_data )

        else:

            if self.options.test:
                ret = False
            else: 
                if self.options.verbose: 
                    print("Adding new...")

                self.pvo_url = self.create_richard(video_data)
                print('new richard url', self.pvo_url)
                ep.public_url = self.pvo_url
                ret = self.pvo_url

        ep.save()

        return ret

    def update_richard(self, v_id, new_data):
        """ updates a richard record
        :arg vid: video id for richard
        :arg new_data: dict of fields to update

        :returns: a dict from the updated video

        """
        # fetch current record
        video_data = get_video(
                api_url=self.richard_endpoint, 
                auth_token=self.host['api_key'], 
                video_id=v_id)

        # if self.options.verbose: pprint.pprint( video_data )
     
        if video_data['state'] == STATE_LIVE:
            print("Currently STATE_LIVE, 403 coming.")

        if self.options.test:
            print('test mode, not updating richard') 
            print('veyepar:', pprint.pprint(new_data))
            print('ricard:', pprint.pprint(video_data))
            ret = False
        else: 
            print('2. updating richard', v_id)
            if self.options.verbose: pprint.pprint( video_data )
            video_data.update(new_data)
            try:
                # update richard with new information
                ret = update_video(self.richard_endpoint, 
                       self.host['api_key'], v_id, video_data)
 
                # above ret= isn't working.  returns None I think?
                # lets hope there wasn't a problem and blaze ahead.
                ret = True

            except MissingRequiredData as e:
                print('#2, Missing required fields', e.errors)
                import code
                code.interact(local=locals())
                raise e

            except Http4xxException as e:
                if video_data['state'] == STATE_LIVE:
                    if e.response.status_code == 403:
                        print("told you 403 was coming.")
                        print("maybe you can fix it with this:")
                        print("http://{host}/admin/videos/video/{id}/".format(host=self.host['host'],id=v_id)) 
                        print("don't forget to unlock veyepar too.")
                    else:
                        print("expected 403 due to STATE_LIVE, but now...")

                print(e.response.status_code)
                print(e.response.content)
                import code
                code.interact(local=locals())
                raise e

        return ret

    def create_richard(self, video_data):
        """ creates a richard record
        :arg video_data: dict of video information to be added

        :returns: a richard url for the video

        """
        try:
            vid = create_video(self.richard_endpoint, 
                    self.host['api_key'], video_data)
            url = 'http://%s/video/%s/%s' % (
                    self.host['host'], vid['id'],vid['slug'])
            return url

        except MissingRequiredData as e:
            print('#3, Missing required fields', e)
            raise e
        except Http4xxException as exc:
            print(exc.response.status_code)
            print(exc.response.content)

    def create_richard_episode_dict(self, ep, state=1):
        """ create dict for richard based on Episode

        This creates a dict of based on information available in an Episode
        object. This does not populate information that has to be derived
        from scrapping.

        :arg ep: Episode to convert in to a richard dict
        :arg state: richard state. 1=live, 2=draft. defaults to 1
        :returns: dict of Episode information for use by richard

        """

        # clean up messy Episode data
        speakers = self.clean_richard_speakers(ep)
        tags = self.clean_richard_tags(ep)
        description = self.clean_richard_description(ep)
        
        duration = ep.cuts_time()
        # If there are no cuts defined yet 
        # (like before the event)
        #   use the sheduled time.
        if duration is None:
            duration = int(ep.get_minutes()*60)
        
        video_data = {
            'state': state,
            'title': ep.name,
            'category': self.category_key,
            'description': description,
            'summary': "",
            'source_url': ep.host_url,
            'copyright_text': ep.license,
            'tags': tags,
            'speakers': speakers,
            'recorded': ep.start.strftime("%Y-%m-%d"),
            'language': 'English',
            'duration': duration,
            # 'video_webm_url': ep.rax_mp4_url, # only rax_xxx_url
            'video_mp4_url': ep.rax_mp4_url,
            'video_mp4_download_only': False,
        }
        if ep.show.slug=="debconf14":
            video_data['video_webm_url'] = "http://meetings-archive.debian.net/pub/debian-meetings/2014/debconf14/webm/{}.webm".format(ep.slug)

        return video_data

    def clean_archive_mp4_url(self, ep):
        # strip off parameters that archive adds.
        # maybe this should go into archive_uploader.py ?

        if ep.archive_mp4_url:
            o = urlparse(ep.archive_mp4_url)
            mp4url = "%(scheme)s://%(netloc)s%(path)s" % o._asdict()
        else:
            mp4url = ""

        return mp4url

    def clean_richard_description(self, ep):
        # Richard wants markdown
        # so if ep data is in html or somthing, convert to markdown.
        # best to get event site to provide markdown.
        # desc = linebreaks(urlize(force_escape(ep.description)))
        return ep.description

    def clean_richard_speakers(self, ep):
        """ sanitize veyepar authors to create richard speakers

        :arg ep: Episode with authors, comma sepperated 
        :returns: list of speakers

        """
        # speakers = [] if ep.authors is None else ep.authors.split(',')
        speakers = ep.authors.split(',') if ep.authors else []
        speakers = [ s.strip() for s in speakers ]
        return speakers

    def clean_richard_tags(self, ep):
        """ sanitize veyepar tags for use by richard

        :arg ep: Episode with veyepar tags
        :returns: list of richard tags

        """

        # remove blacklisted tags, and tags with a / in them. and strip spaces 
        if ep.tags is None:
            tags = ''
        else:
            tags = ep.tags.split(',')
            tags = [t.strip() for t in tags]
            tags = [t for t in tags 
                    if t not in [
                     'enthought', 'scipy_2012', 
                     'Introductory/Intermediate',
                     ] 
                     and '/' not in t 
                     and t]

            # *fix* long tags (prolly not really tags)
            tags2 = []
            for t in tags:
                if len(t)>30:
                    # grab the first word.
                    t = t.split()[0]
                tags2.append(t)
            tags = tags2

        return tags

    def get_scrapevideo_metadata(self, host_url):
        """ scrapes metadata from the host_url of the episode

        This is a wrapper around steve's scrapevideo. It preps
        the host_url if necessary, and repeatedly calls scrapevideo
        until no error is raised

        :arg ep: Episode of video to scrape
        :returns: dict of metadata, or {}

        """

        if host_url is None or host_url == '':
            # there's nothing to scrape
            return {}

        # FIXME: error handling kinda crazy here
        while True:
            # keep trying until it doesn't error doh!
            try:
                scraped_meta = scrapevideo(host_url)
                break
            except KeyError as e: 
                print("KeyError", e)
            except requests.exceptions.Timeout as e: 
                # requests.exceptions.Timeout: HTTPConnectionPool(host='www.youtube.com', port=80): Request timed out. (timeout=3)
                print("requests.exceptions.Timeout:", e)
                print("looping...")


            
        if self.options.verbose: 
            print("scraped_meta")
            pprint.pprint( scraped_meta )

        return scraped_meta

    def is_already_in_richard(self, ep):

        if self.options.add_all: 
            ret = False
        else:
            # its truthiness implies that the video already exists in richard
            ret = ep.public_url

        if self.options.verbose: 
            print("is_already_in_richard", ret)

        return ret


    def add_more_options(self, parser):

        # parser.add_option('--all', action="store_true",
        # oh wait.. I am not sure how to implement this...
        #  help="process all, regardless of state. (does not change state)")

        # reload wtd cuz we trashed 2013.. opps!
        parser.add_option('--add-all', action="store_true",
           help="Assume it doesn't exist, overwrite previous richard url.")

        # straight to public
        parser.add_option('--public', action="store_true",
           help="Set state to public on upload.")

        # use title slide preview as thumb (for metadata preview)
        parser.add_option('--title-thumb', action="store_true",
           help="Use title slide preview url as thumb.")

        # push to alterate richard (like to test crazy edit feature)
        parser.add_option('--richard-id',
           help="Override client.")


if __name__ == '__main__':
    p = add_to_richard()
    p.main()

