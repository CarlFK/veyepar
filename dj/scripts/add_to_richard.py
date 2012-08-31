#!/usr/bin/python

# push metadata to richard (like pyvideo.org)

# This is just a lib that makes doing REST stuff easier.
import slumber

import pprint

from steve.util import scrapevideo
import json

import pw

from process import process

from main.models import Show, Location, Episode

class add_to_richard(process):

    ready_state = 5

    def process_ep(self, ep):
        if self.options.verbose: print "post_to_richard", ep.id, ep.name

        ### remove some day....
        if ep.host_url.startswith("http://gdata.youtube.com/feeds/api/videos/"):
            yt_id = ep.host_url.split('/')[-1]
            ep.host_url="http://youtube.com/watch?v=%s" % (yt_id,)
            
        # get the metadata from youtube
        # like thumb url and video embed code
        yt_meta = scrapevideo(ep.host_url)
        if self.options.verbose: 
            pprint.pprint( yt_meta )
        
        speakers = '' if ep.authors is None else ep.authors.split(',')

        tags = ep.tags.split(',')
        # remove blacklisted tags, 
        # and tags with a / in them.
        tags = [t for t in tags if t not in [
             u'enthought', 
             u'scipy_2012', 
             u'Introductory/Intermediate',
             ] 
             and '/' not in t 
             and t]

        host = pw.richard[self.options.host_user]
        pprint.pprint(host)

        # Create an api object with the target api root url.
        endpoint = 'http://%(host)s/api/v1/' % host 
        api = slumber.API(endpoint)

        # make sure the category exists.
        # This seems like a terible way to doing this, 
        # but I need to get something working today!!!
        # I am going to regret this later.
        # To the future me: Sorry.

        print "Show slug:", ep.show.slug
        cats = api.category.get(limit=0)
        found = False
        for cat in cats['objects']:
            print "|",cat['id'], cat['slug'],
            if cat['slug']  ==  ep.show.slug:
               found = True
               print "found it!"

        if not found:
            # The category doesn't exist yet, so create it
            cat_data = {
                'kind': 1,
                'name': ep.show.name,
                'title': ep.show.name,
                'description': '',
                'url': 'http://conference.scipy.org/scipy2012/',
                'whiteboard': '',
                'start_date': '2012-07-16',
                'slug': ep.show.slug
            }
            try:
                cat = api.category.post(cat_data, 
                    username=host['user'], api_key=host['api_key'])
                pass
            except Exception as exc:
                # TODO: OMG gross.
                if exc.content.startswlth('\n<!DOCTYPE html>'):
                    error_lines = [line for line in exc.content.splitlines()
                            if 'exception_value' in line]
                    for line in error_lines:
                         print line
                else:
                    print "exc.content:", exc.content.__repr__()

                raise



        # Let's populate a video object and push it.
        video_data = {
    'state': 1,
    'title': ep.name,
    'category': ep.show.name,
    'summary': ep.description,
    #'slug': ep.slug,
    'source_url': ep.host_url,
    'copyright_text': ep.license,
    'tags': tags,
    'speakers': speakers,
    'recorded': ep.start.isoformat(),
    'language': 'English',
    'whiteboard': u'',
    'quality_notes': '',
    'description': u'',
    'thumbnail_url': yt_meta['thumbnail_url'],
    'video_ogv_url': ep.archive_ogv_url,
    'video_ogv_length': None,
    'video_mp4_url': ep.archive_mp4_url,
    'video_mp4_download_only': False,
    'video_mp4_length': None,
    'video_webm_url': u'',
    'video_webm_length': None,
    'video_flv_url': u'',
    'video_flv_length': None,
    'embed': yt_meta.get('object_embed_code',''),
}
        if self.options.verbose: pprint.pprint(video_data)

        # Let's create this video with an HTTP POST.
        
        try:
            vid = api.video.post(video_data, 
                    username=host['user'], api_key=host['api_key'])

            self.pvo_url = "http://%s/video/%s/%s" % (
                    host['host'], vid['id'],vid['slug'])
            if self.options.verbose: print self.pvo_url
            ep.public_url = self.pvo_url
            ret = self.pvo_url

        except Exception as exc:
            print exc
            ret = False
            # TODO: OMG gross.
            if exc.content.startswith('\n<!DOCTYPE html>'):
                error_lines = [line for line in exc.content.splitlines()
                        if 'exception_value' in line]
                for line in error_lines:
                     print line
            else:
                print exc.content

            raise

        ep.save()

        return ret

if __name__ == '__main__':
    p=add_to_richard()
    p.main()

