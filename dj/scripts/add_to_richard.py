#!/usr/bin/python

# push metadata to richard (like pyvideo.org)

import datetime
import pprint
from urlparse import urlparse, parse_qs
from process import process as Process

from steve.richardapi import create_category_if_missing, create_video, update_video, MissingRequiredData
from steve.util import scrapevideo
from steve.restapi import API, get_content

from django.template.defaultfilters import linebreaks, urlize, force_escape

from main.models import Show, Location, Episode

import pw

class Richard(Process):

    ready_state = 5
    # ready_state = None

    def process_ep(self, ep):
        """ adds Episode to pyvideo

        :arg ep: Episode to add to pyvideo
        :returns: different things based on what is happening
                  a video dictionary for updated videos
                  a pyvideo url for newly added videos
                  False if there was an exception during processing

        """
        if self.options.verbose:
            print "RichardProcess", ep.id, ep.name
            print "Show slug:", ep.show.slug, ep.show.client.name

        # pyvideo categories are stored in Client and Show
        # chipy is an example of something that uses Client,
        # pycon 2014 and 300SoC are in Show.
        self.category_key = ep.show.category_key \
                or ep.show.client.category_key

        self.host = pw.richard[ep.show.client.richard_id]

        self.pyvideo_endpoint = 'http://{hostname}/api/v1'.format(hostname=self.host['host'])
        self.api = API(self.pyvideo_endpoint)

        if self.options.verbose: 
            print self.pyvideo_endpoint, self.host['user'], self.host['api_key'], {'category_key': self.category_key}

        # FIXME using chatty hack due to problems with category handling
        if not self.options.test:
            create_category_if_missing( self.pyvideo_endpoint, 
                    self.host['user'], self.host['api_key'], 
                    {'title': self.category_key})
        
        video_data = self.create_pyvideo_episode_dict(ep, state=2)
        # perhaps we could just update the dict based on scraped_meta
        # scraped_metadata = self.get_scrapevideo_metadata(ep.host_url)
        # video_data['thumbnail_url'] = scraped_metadata.get('thumbnail_url','')

        print ep.id, ep.host_url

        if ep.host_url is None:
            video_data['thumbnail_url'] = "http://veyepar.nextdayvideo.com/static/%s/%s/titles/%s.png" % ( ep.show.client.slug, ep.show.slug, ep.slug )

        elif "youtube" in ep.host_url:  
            scraped_metadata = self.get_scrapevideo_metadata(ep.host_url)
            video_data['thumbnail_url'] = scraped_metadata.get('thumbnail_url','')
            video_data['embed'] = \
                    scraped_metadata.get('object_embed_code','')

        elif "vimeo" in ep.host_url:  
            # video_data['embed'] = scraped_metadata.get('embed_code','')
            params = {'vimeo_id': ep.host_url.split('/')[-1]}
            video_data['embed'] ="""<object width="640" height="480"><param name="allowfullscreen" value="true"><param name="allowscriptaccess" value="always"><param name="movie" value="http://vimeo.com/moogaloop.swf?show_byline=1&amp;fullscreen=1&amp;clip_id=%(vimeo_id)s&amp;color=&amp;server=vimeo.com&amp;show_title=1&amp;show_portrait=0"><embed src="http://vimeo.com/moogaloop.swf?show_byline=1&amp;fullscreen=1&amp;clip_id=%(vimeo_id)s&amp;color=&amp;server=vimeo.com&amp;show_title=1&amp;show_portrait=0" allowscriptaccess="always" height="480" width="640" allowfullscreen="true" type="application/x-shockwave-flash"></embed></object>""" % params 

        if self.options.verbose: pprint.pprint(video_data)

        if \
            not video_data['video_mp4_url'] \
            or not video_data['source_url'] \
            or not video_data['embed']:
                import code
                # code.interact(local=locals())

        try:

            if self.is_already_in_pyvideo(ep):
                vid_id = ep.public_url.split('/video/')[1].split('/')[0]
                print 'updating episode in pyvideo', ep.public_url, vid_id
                if not self.options.test:
                    ret = self.update_pyvideo(vid_id, video_data)
                    # above ret= isn't working.  returns None I think?
                    # lets hope there wasn't a problem and blaze ahead.
                    ret = True
                else: 
                    ret = False
            else:
                if not self.options.test:
                    self.pvo_url = self.create_pyvideo(video_data)
                    print 'new pyvideo url', self.pvo_url
                    ep.public_url = self.pvo_url
                    ret = self.pvo_url
                else: 
                    ret = False

        except Exception as exc:
            print "exc:", exc
            import code
            code.interact(local=locals())
            raise exc

        ep.save()

        return ret

    def update_pyvideo(self, vid, new_data):
        """ updates a pyvideo record
        :arg vid: video id for pyvideo
        :arg new_data: dict of fields to update

        :returns: a dict from the updated video

        """
        try:
            # fetch current record
            response = self.api.video(vid).get(username=self.host['user'], api_key=self.host['api_key'])
            video_data = get_content(response)
            if self.options.verbose: pprint.pprint( video_data )
            # update dict with new information
            video_data.update(new_data)
            if self.options.verbose: pprint.pprint( video_data )
            # update in pyvideo
            return update_video(self.pyvideo_endpoint, self.host['user'], self.host['api_key'], vid, video_data)
        except MissingRequiredData as e:
            print 'Missing required fields', e.errors
            raise e

    def create_pyvideo(self, video_data):
        """ creates a pyvideo record
        :arg video_data: dict of video information to be added

        :returns: a pyvideo url for the video

        """
        try:
            video_data['added'] = datetime.datetime.now().isoformat()
            vid = create_video(self.pyvideo_endpoint, self.host['user'], self.host['api_key'], video_data)
            return 'http://%s/video/%s/%s' % (self.host['host'], vid['id'],vid['slug'])
        except MissingRequiredData as e:
            print 'Missing required fields', e.errors
            raise e

    def create_pyvideo_episode_dict(self, ep, state=1):
        """ create dict for pyvideo based on Episode

        This creates a dict of based on information available in an Episode
        object. This does not populate information that has to be derived
        from scrapping.

        :arg ep: Episode to convert in to a pyvideo dict
        :arg state: pyvideo state. 1=live, 2=draft. defaults to 1
        :returns: dict of Episode information for use by pyvideo

        """

        # clean up messy Episode data
        speakers = self.clean_pyvideo_speakers(ep)
        tags = self.clean_pyvideo_tags(ep)
        summary = self.clean_pyvideo_summary(ep)
        mp4url = self.clean_archive_mp4_url(ep)
        
        video_data = {
            'state': state,
            'title': ep.name,
            'category': self.category_key,
            'summary': summary,
            'source_url': ep.host_url,
            'copyright_text': ep.license,
            'tags': tags,
            'speakers': speakers,
            'recorded': ep.start.isoformat(),
            'language': 'English',
            'duration': int(ep.get_minutes()),
            'video_ogv_url': ep.archive_ogv_url,
            'video_mp4_url': mp4url, 
            'video_mp4_download_only': True,
        }
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

    def clean_pyvideo_summary(self, ep):
        # Richard wants markdown
        # so if ep data is in html or somthing, convert to markdown.
        # best to get event site to provide markdown.
        # desc = linebreaks(urlize(force_escape(ep.description)))
        return ep.description

    def clean_pyvideo_speakers(self, ep):
        """ sanitize veyepar authors to create pyvideo speakers

        :arg ep: Episode with authors, comma sepperated 
        :returns: list of speakers

        """
        # speakers = [] if ep.authors is None else ep.authors.split(',')
        speakers = ep.authors.split(',') if ep.authors else []
        speakers = [ s.strip() for s in speakers ]
        return speakers

    def clean_pyvideo_tags(self, ep):
        """ sanitize veyepar tags for use by pyvideo

        :arg ep: Episode with veyepar tags
        :returns: list of pyvideo tags

        """

        # remove blacklisted tags, and tags with a / in them. and strip spaces 
        if ep.tags is None:
            tags = ''
        else:
            tags = ep.tags.split(',')
            tags = [t.strip() for t in tags 
                    if t not in [
                     u'enthought', u'scipy_2012', 
                     u'Introductory/Intermediate',
                     ] 
                     and '/' not in t 
                     and t]

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
                print "KeyError", e
            
        if self.options.verbose: 
            pprint.pprint( scraped_meta )

        return scraped_meta

    def is_already_in_pyvideo(self, ep):
        # its truthiness implies that the video already exists in pyvideo
        return ep.public_url

if __name__ == '__main__':
    p = Richard()
    p.main()

