#!/usr/bin/python

# push metadata to richard (like pyvideo.org)

# This is just a lib that makes doing REST stuff easier.
# import slumber
import requests

import pprint

from django.template.defaultfilters import \
        linebreaks, urlize, force_escape

from steve.util import scrapevideo

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
        while True:
            # keep trying untill it doesn't error doh!
            try:
                yt_meta = scrapevideo(ep.host_url)
                break
            except KeyError as e: 
                print "KeyError", e
            
        if self.options.verbose: 
            pprint.pprint( yt_meta )
        
        # speakers = [] if ep.authors is None else ep.authors.split(',')
        speakers = ep.authors.split(',') if ep.authors else []

        tags = ep.tags.split(',')
        # remove blacklisted tags, 
        # and tags with a / in them.
        # and strip spaces 
        tags = [t.strip() for t in tags if t not in [
             u'enthought', 
             u'scipy_2012', 
             u'Introductory/Intermediate',
             ] 
             and '/' not in t 
             and t]

        host = pw.richard[self.options.host_user]

        # Create an api object with the target api root url.
        endpoint = 'http://%(host)s/api/v1/' % host 
        api = slumber.API(endpoint)
        ### api = slumber.API(endpoint, session=requests.session(
        ###   params={"username": host['user'], "api_key": host['api_key']}))

        # make sure the category exists.
        # This seems like a terible way to doing this, 
        # but I need to get something working today!!!
        # I am going to regret this later.
        # To the future me: Sorry.


        """
        if self.options.verbose: print "Show slug:", ep.show.slug, ep.show.client.name
        cats = api.category.get(limit=0)
        found = False
        for cat in cats['objects']:
            if self.options.verbose: print cat['id'], cat['slug'], cat['name']
            if cat['name']  ==  ep.show.name:
                found = True
                if self.options.verbose: print "found"
                break

        if not found:
            # The category doesn't exist yet, so create it

            if self.options.verbose:  print "creating..."
            cat_data = {
                'kind': 1,
                'name': ep.show.name,
                # 'name': ep.show.client.name,
                'title': ep.show.name,
                # 'title': ep.show.client.name,
                'description': '',
                'url': '',
                'whiteboard': '',
                # I think start_date should be blank, or .today()
                # 'start_date': '2012-07-16',
                # 'slug': ep.show.client.slug
                # 'slug': ep.show.slug
            }
            try:
                # cat = api.category.post(cat_data, 
                #    username=host['user'], api_key=host['api_key'])
                # if self.options.verbose:  print "created", cat
                pass
            except Exception as exc:
                # TODO: OMG gross.
                if exc.content.startswith('\n<!DOCTYPE html>'):
                    error_lines = [line for line in exc.content.splitlines()
                            if 'exception_value' in line]
                    for line in error_lines:
                         print line
                else:
                    print "exc.content:", exc.content.__repr__()

                raise

        # cat is now the category we want to use
        # either it was existing, or was just added.
        # category_key = cat['title']
        """

        # category_key = 'PyCon DE 2012'
        # category_key = 'PyCon DE 2012'
        category_key = 'ChiPy'
     
        description = (
            linebreaks(
            urlize(
            force_escape(ep.description))))
        slug = ep.slug.replace("_","-").lower()

        # Let's populate a video object and push it.
        video_data = {
    'state': 1, # 1=live, 2=draft
    'title': ep.name,
    'category': category_key,
    'summary': description,
    # 'slug': slug,  
    'source_url': ep.host_url,
    'copyright_text': ep.license,
    'tags': tags,
    'speakers': speakers,
    'recorded': ep.start.isoformat(),
    'language': 'English',
     #'language': 'German',
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


        try:
            if ep.public_url:
                # update
                vid_id = ep.public_url.split('/video/')[1].split('/')[0]
                updated = api.video(vid_id).put(video_data,
                    username=host['user'], api_key=host['api_key'])
                ret = updated
            else:
                # add
                vid = api.video.post(video_data,
                        username=host['user'], api_key=host['api_key'])
                # set to draft
                updated = api.video(vid['id']).put({
                    'state':2, 
                    'category': vid['category'],
                    'title': vid['title'],
                            },  
                        username=host['user'], api_key=host['api_key'])

                self.pvo_url = "http://%s/video/%s/%s" % (
                        host['host'], vid['id'],vid['slug'])
                if self.options.verbose: print self.pvo_url
                print self.pvo_url
                ep.public_url = self.pvo_url
                ret = self.pvo_url

        except Exception as exc:
            print "exc:", exc
            ret = False
            import code
            code.interact(local=locals())

            # TODO: OMG gross.
            if exc.content.startswith('\n<!DOCTYPE html>'):
                error_lines = [line for line in exc.content.splitlines()
                        if 'exception_value' in line]
                for line in error_lines:
                     print line
            else:
                print "exc.content:", exc.content

            raise

        ep.save()

        return ret

if __name__ == '__main__':
    p=add_to_richard()
    p.main()

