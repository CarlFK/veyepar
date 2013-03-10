#!/usr/bin/python

# push metadata to richard (like pyvideo.org)

import datetime
from django.template.defaultfilters import linebreaks, urlize, force_escape
from steve.richardapi import create_category_if_missing, create_video
from steve.util import scrapevideo
from steve.restapi import API, get_content

import pprint
import pw

from process import process as Process
from main.models import Show, Location, Episode


class RichardProcess(Process):

    ready_state = 5
    # ready_state = None

    # pyvideo categories are either Show.name or Client.name
    # chipy is an example of something that uses the Client.name.
    # pycon 2013 is an example of something that uses the Show.name.
    # 
    # hardcoding category until we figure out a better system

    category_key = 'ChiPy'
    # category_key = 'PyCon 2013'


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

        self.host = pw.richard[self.options.host_user]
        self.pyvideo_endpoint = 'http://{hostname}/api/v1'.format(hostname=self.host['host'])
        self.api = API(self.pyvideo_endpoint)

        """
        FIXME LATER - removed for now, not needed for PyCon.
        # FIXME using chatty hack due to problems with category handling
        if self.options.verbose: 
            print self.pyvideo_endpoint, self.host['user'], self.host['api_key'], {'title': self.category_key}

        create_category_if_missing(self.pyvideo_endpoint, 
                self.host['user'], self.host['api_key'], 
                {'title': self.category_key})
        """
        
        video_data = self.create_pyvideo_episode_dict(ep)
        # perhaps we could just update the dict based on scraped_meta
        scraped_metadata = self.get_scrapevideo_metadata(ep)
        video_data['thumbnail_url'] = scraped_metadata.get('thumbnail_url','')
        video_data['embed'] = scraped_metadata.get('object_embed_code','')

        if self.options.verbose: pprint.pprint(video_data)

        if self.is_already_in_pyvideo(ep):
            vid_id = ep.public_url.split('/video/')[1].split('/')[0]
            if self.options.verbose: 
                print 'episode already exists in pyvideo', ep.public_url, vid_id
            ret = self.fetch_and_update_pyvideo(vid_id, video_data)
        else:
            vid = self.create_pyvideo(video_data)
            self.pvo_url = "http://%s/video/%s/%s" % (self.host['host'], vid['id'],vid['slug'])
            print self.pvo_url
            ep.public_url = self.pvo_url
            ret = self.pvo_url

        # except Exception as exc:
        if self.options.debug:
            # print "exc:", exc
            ret = False
            import code
            code.interact(local=locals())
            # raise

        ep.save()

        return ret

    def fetch_and_update_pyvideo(self, vid_id, new_data):
        """ fetches the record from pyvideo and updates it with the new_data

        :arg vid_id: pyvideo id
        :arg video_data: dict containing updated video data
        :returns: dict of response from pyvideo

        """
        print vid_id
        old_video = self.api.video(vid_id).get()
        print old_video
        old_content = get_content(old_video)
        old_video.update(new_data)

        if self.options.verbose: 
            pprint.pprint(old_video)

        return self.api.video(vid_id).put(data=old_video)

    def create_pyvideo(self, video_data):
        """ adds a new video to pyvideo

        :arg video_data: a dict with video data for pyvideo
        :returns: dict of video response from pyvideo

        """
        video_data['added'] = datetime.datetime.now().isoformat()
        video = create_video(self.pyvideo_endpoint, self.host['user'], self.host['api_key'], video_data)
        if self.options.verbose: print video
        return video


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
            'video_ogv_url': ep.archive_ogv_url,
            'video_mp4_url': ep.archive_mp4_url,
            'video_mp4_download_only': False,
        }
        return video_data

    def clean_pyvideo_summary(self, ep):
        # return linebreaks(urlize(force_escape(ep.description)))
        return ep.description

    def clean_pyvideo_speakers(self, ep):
        """ sanitize veyepar authors to create pyvideo speakers

        :arg ep: Episode with authors
        :returns: list of pyvideo speakers

        """
        # speakers = [] if ep.authors is None else ep.authors.split(',')
        return ep.authors.split(',') if ep.authors else []

    def clean_pyvideo_tags(self, ep):
        """ sanitize veyepar tags for use by pyvideo

        :arg ep: Episode with veyepar tags
        :returns: list of pyvideo tags

        """

        # remove blacklisted tags, and tags with a / in them. and strip spaces 
        tags = ep.tags.split(',')
        tags = [t.strip() for t in tags if t not in [
             u'enthought', 
             u'scipy_2012', 
             u'Introductory/Intermediate',
             ] 
             and '/' not in t 
             and t]
        return tags

    def get_scrapevideo_metadata(self, ep):
        """ scrapes metadata from the host_url of the episode

        This is a wrapper around steve's scrapevideo. It preps
        the host_url if necessary, and repeatedly calls scrapevideo
        until no error is raised

        :arg ep: Episode of video to scrape
        :returns: dict of metadata, or {}

        """

        if ep.host_url is None:
            # there's nothing to scrape
            return {}

        # FIXME: error handling kinda crazy here
        while True:
            # keep trying until it doesn't error doh!
            try:
                scraped_meta = scrapevideo(ep.host_url)
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
    p = RichardProcess()
    p.main()

