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

        # get the metadata from youtube
        # like thumb url and video embed code
        json_data = scrapevideo(ep.host_url)
        yt_meta = json.loads( json_data )
        #  pprint.pprint( yt_meta )
        
        host = pw.richard[self.options.host_user]
        pprint.pprint(host)

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
    'whiteboard': u'',
    'quality_notes': '',
    'description': u'',
    'thumbnail_url': yt_meta['thumbnail_url'],
    'video_ogv_url': u'',
    'video_ogv_length': None,
    'video_mp4_url': ep.archive_url,
    'video_mp4_download_only': True,
    'video_mp4_length': None,
    'video_webm_url': u'',
    'video_webm_length': None,
    'video_flv_url': u'',
    'video_flv_length': None,
    'embed': yt_meta['object_embed_code'],
}

        video_data = {
 'category': u'Chipy_aug_2012',
 'copyright_text': u'',
 'description': u'',
 'embed': u'<object width="640" height="390"><param name="movie" value="http://youtube.com/v/0CZgmbl47xw?version=3&amp;hl=en_US"></param><param name="allowFullScreen" value="true"></param><param name="allowscriptaccess" value="always"></param><embed src="http://youtube.com/v/0CZgmbl47xw?version=3&amp;hl=en_US" type="application/x-shockwave-flash" width="640" height="390" allowscriptaccess="always" allowfullscreen="true"></embed></object>',
 'language': 'English',
 'quality_notes': '',
 'recorded': '2012-08-09T20:00:00',
 'slug': u'Mono_to_IronPython',
 'source_url': u'https://www.youtube.com/watch?v=0CZgmbl47xw',
 'speakers': [u'Fawad Halim'],
 'state': 1,
 'summary': u'Introduction to Mono, what it means in relation to .NET, with a segway into IronPython.',
 'tags': [u''],
 'thumbnail_url': u'http://i1.ytimg.com/vi/0CZgmbl47xw/hqdefault.jpg',
 'title': u'Mono to IronPython',
 'video_flv_length': None,
 'video_flv_url': u'',
 'video_mp4_download_only': True,
 'video_mp4_length': None,
 'video_mp4_url': u'http://test.bucket.s3.us.archive.org/chipy/chipy_aug_2012/Mono_to_IronPython?Signature=%2FejIq9oN0LEH5OR6OSiRzqr8td8%3D&Expires=1344725073&AWSAccessKeyId=FEWGReWX3QbNk0h3',
 'video_ogv_length': None,
 'video_ogv_url': u'',
 'video_webm_length': None,
 'video_webm_url': u'',
 'whiteboard': u''}

        pprint.pprint(video_data)

        # Let's create this video with an HTTP POST.
        try:
            print "trying..."
            vid = api.video.post(video_data, 
                username=host['user'],
                api_key=host['api_key'])
        except Exception as exc:
            # TODO: OMG gross.
            error_lines = [line for line in exc.content.splitlines()
                           if 'exception_value' in line]
            if error_lines:
                for line in error_lines:
                    print line
            raise


        print "Created video: ", vid
        ep.public_url = vid

        ep.save()

        ret = True
        return ret

if __name__ == '__main__':
    p=add_to_richard()
    p.main()

