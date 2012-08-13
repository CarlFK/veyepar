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

        # get the thumb url from youtube
        json_data = scrapevideo(ep.host_url)
        yt_meta = json.loads( json_data )
        #  pprint.pprint( yt_meta )
        
        host = pw.richard[self.options.host_user]
        # pprint.pprint(host)

        # Create an api object with the target api root url.
        api = slumber.API(host['url'])

        # make sure the category exists.
        # This seems like a terible way to doing this, 
        # but I need to get something working today!!!
        # I am going to regret this later.
        # To the future me: Sorry.


        cats = api.category.get()
        found = False
        for cat in cats['objects']:
            if cat['slug']  ==  ep.show.slug:
               found = True

        if not found:
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
            cat = api.category.post(cat_data, 
                    username=host['user'],
                    api_key=host['api_key'])


        # Let's populate a video object and push it.
        video_data = {
    'state': 1,
    'title': ep.name,
    'category': ep.show.name,
    'summary': ep.description,
    'slug': ep.slug,
    'source_url': ep.host_url,
    'copyright_text': ep.license,
    'tags': ep.tags.split(','),
    'speakers': ep.authors.split(','),
    # 'added': '2012-06-15T20:34:32',
    'recorded': ep.start.isoformat(),
    'language': 'English',
    'thumbnail_url': yt_meta['thumbnail_url'],
    'video_ogv_url': u'',
    'video_ogv_length': None,
    'video_mp4_url': ep.archive_url,
    'video_mp4_length': None,
    'video_webm_url': u'',
    'video_webm_length': None,
    'video_flv_url': u'',
    'video_flv_length': None,
    # 'embed': yt_meta['embed_code'],
    'embed': yt_meta['object_embed_code'],
}

        pprint.pprint(video_data)

        # Let's create this video with an HTTP POST.
        vid = api.video.post(video_data, 
                username=host['user'],
                api_key=host['api_key'])

        print "Created video: ", vid
        ep.public_url = vid

        ep.save()

        ret = True
        return ret

if __name__ == '__main__':
    p=add_to_richard()
    p.main()

