#!/usr/bin/python

# push metadata to richard (like pyvideo.org)

import datetime
from django.template.defaultfilters import linebreaks, urlize, force_escape
from steve.richardapi import create_category_if_missing, create_video
from steve.util import scrapevideo
from steve.restapi import API

# for when you do the pep8 overhaul
from process import process as Process
import pprint
import pw


class RichardProcess(Process):

    ready_state = 5

    # pyvideo categories are either Show.name or Client.name
    # chipy is an example of something that uses the Client.name.
    # pycon 2013 is an example of something that uses the Show.name.
    # 
    # hardcoding category until we figure out a better system
    category_key = 'ChiPy'


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

        host = pw.richard[self.options.host_user]

        # FIXME using chatty hack due to problems with category handling
        self.create_pyvideo_category_if_missing(self.category_key)
        
        video_data = self.create_pyvideo_episode_dict(ep)
        # perhaps we could just update the dict based on scraped_meta
        # but I fear change
        scraped_metadata = self.get_scrapevideo_metadata(ep)
        video_data['thumbnail_url'] = scraped_metadata.get('thumbnail_url','')
        video_data['embed'] = scraped_metadata.get('object_embed_code','')

        if self.options.verbose: pprint.pprint(video_data)

        try:
            if self.is_already_in_pyvideo(ep):
                vid_id = ep.public_url.split('/video/')[1].split('/')[0]
                ret = self.update_pyvideo(vid_id, video_data)
            else:
                # FIXME: using chatty hack due to slumber kruft.
                # creating videos in draft mode was barfing with slumber.
                # now that we are using steve we should revisit that
                vid = self.create_video(video_data)
                # update video to draft mode
                self.update_pyvideo(vid['id'], {'state':2,
                    'category': vid['category'],
                    'title': vid['title'],})

                self.pvo_url = "http://%s/video/%s/%s" % (host['host'], vid['id'],vid['slug'])
                print self.pvo_url
                ep.public_url = self.pvo_url
                ret = self.pvo_url

        except Exception as exc:
            print "exc:", exc
            ret = False
            import code
            code.interact(local=locals())

            # print redundant?
            print exc.errors
            raise

        ep.save()

        return ret

    def update_pyvideo(self, vid_id, video_data):
        """ updates the video in pyvideo

        wrapper around the steve.restapi since steve.richardapi doesn't have
        an update_video equivalent yet

        :arg vid_id: pyvideo id
        :arg video_data: dict containing updated information
        :returns: dict of response from pyvideo

        """
        host = pw.richard[self.options.host_user]
        pyvideo_endpoint = 'http://{hostname}/v1/api/'.format(hostname=host['host'])
        api = API(pyvideo_endpoint)
        updated = api.video(vid_id).put(video_data, username=host['user'], api_key=host['api_key'])
        return updated

    def create_pyvideo(self, video_data):
        """ adds a new video to pyvideo

        :arg video_data: a dict with video data for pyvideo
        :returns: dict of video response from pyvideo

        """
        host = pw.richard[self.options.host_user]
        pyvideo_endpoint = 'http://{hostname}/v1/api/'.format(hostname=host['host'])
        video_data['added'] = datetime.datetime.now().isoformat()
        video = create_video(pyvideo_endpoint, host['user'], host['api_key'], video_data)
        if self.options.verbose: print video
        return video

    def create_pyvideo_category_if_missing(self, category):
        """ creates a pyvideo category if it doesn't exist otherwise does nothing

        :arg category: video category for pyvideo

        """
        host = pw.richard[self.options.host_user]
        pyvideo_endpoint = 'http://{hostname}/v1/api/'.format(hostname=host['host'])
        create_category_if_missing(pyvideo_endpoint, host['user'], host['api_key'], {'title': category})

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
        return (linebreaks(urlize(force_escape(ep.description))))

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
        :returns: dict of metadata

        """

        # FIXME: side effect. this munges host_url if it is a gdata youtube link
        # is this munging necessary or something that could happen in a vidscraper suite?
        if ep.host_url.startswith("http://gdata.youtube.com/feeds/api/videos/"):
            yt_id = ep.host_url.split('/')[-1]
            ep.host_url="http://youtube.com/watch?v=%s" % (yt_id,)

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

