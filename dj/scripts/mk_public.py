#!/usr/bin/python

# mk_public.py - flip state on hosts from private to public
# private = not listed, can be seen if you know the url
#     the presenters have been emaild the URL, 
#     they are encouraged to advertise it.
# public = advertised, it is ready for the world to view.  
#     It will be tweeted at @NextDayVideo

from steve.richardapi import update_video
from steve.restapi import API, get_content

import youtube_uploader

import gdata.youtube
from gdata.media import YOUTUBE_NAMESPACE
from atom import ExtensionElement
import atom

import pw

from process import process

from main.models import Show, Location, Episode, Raw_File, Cut_List

class mk_public(process):

    ready_state = 9

    def up_richard(self, ep):
        self.host = pw.richard[self.options.host_user]
        self.pyvideo_endpoint = 'http://{hostname}/api/v1'.format(hostname=self.host['host'])
        self.api = API(self.pyvideo_endpoint)
        vid_id = ep.public_url.split('/video/')[1].split('/')[0]
        response = self.api.video(vid_id).get(username=self.host['user'], api_key=self.host['api_key'])
        video_data = get_content(response)
        video_data['state'] = 1
        return update_video(self.pyvideo_endpoint, self.host['user'], self.host['api_key'], vid_id, video_data)

    def up_youtube(self, ep):

        uploader = youtube_uploader.Uploader()
        uploader.user = self.options.host_user
        yt_service = uploader.auth()

        id = ep.host_url.split('=')[1]
        uri= 'http://gdata.youtube.com/feeds/api/users/default/uploads/%s' % (id,)
        new_entry=yt_service.GetYouTubeVideoEntry(uri=uri)

        new_entry.extension_elements = [ExtensionElement('accessControl',
            namespace=YOUTUBE_NAMESPACE,
            attributes={'action':'list','permission':'allowed'})]

        updated_entry = yt_service.UpdateVideoEntry(new_entry) 
        return True


    def process_ep(self, ep):
        if self.options.verbose: print ep.id, ep.name
        # set youtube to public
        # set pyvideo state to live
 
        ret = True
        if ep.show.slug == "write_the_docs_2013" or self.up_richard(ep):
        # if self.up_richard(ep):
            if self.up_youtube(ep):
                ret = True

        return ret

if __name__ == '__main__':
    p=mk_public()
    p.main()

