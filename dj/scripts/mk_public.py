#!/usr/bin/python

# mk_public.py - flip state on hosts from private to public
# private = not listed, can be seen if you know the url
#     the presenters have been emaild the URL,
#     they are encouraged to advertise it.
# public = advertised, it is ready for the world to view.
#     It will be tweeted at @NextDayVideo

"""
from steve.richardapi import \
        get_video, update_video, \
        STATE_DRAFT, STATE_LIVE, \
        MissingRequiredData

from steve.restapi import Http4xxException

from add_to_richard import get_video_id
"""

from process import process

import youtube_v3_uploader

import pw

import pprint

from django.conf import settings
from main.models import Show, Location, Episode, Raw_File, Cut_List

class mk_public(process):

    ready_state = 9

    def up_richard(self, ep):

        host = pw.richard[ep.show.client.richard_id]
        endpoint = 'http://{hostname}/api/v2'.format(
                hostname=host['host'])

        v_id = get_video_id(ep.public_url)

        video_data = get_video(api_url=endpoint,
                auth_token=host['api_key'],
                video_id=v_id)

        if video_data['state'] == STATE_LIVE:
            print("Already STATE_LIVE, 403 coming.")
        else:
            video_data['state'] = 1

        try:
            update_video(endpoint,
                    auth_token=host['api_key'],
                    video_id=v_id,
                    video_data=video_data)
        except Http4xxException as exc:
            print(exc)
            print("told you this was coming.")
        except MissingRequiredData as exc:
            print(exc)
            # this shouldn't happen, prolly debugging something.
            import code
            code.interact(local=locals())

        return True

    def up_youtube(self, ep):

        uploader = youtube_v3_uploader.Uploader()
        uploader.client_secrets_file = settings.GOOG_CLIENT_SECRET
        uploader.token_file = pw.yt[ep.show.client.youtube_id]['filename']
        playlist_id = ep.show.youtube_playlist_id
        if self.options.verbose: print("Setting Youtube to public...")
        try:
            ret = uploader.set_permission(ep.host_url)
            if playlist_id:
                uploader.add_to_playlist(ep.host_url, playlist_id)
        except youtube_v3_uploader.HttpError as e:
            print(e)
            pprint(e.error_details)
            import code
            code.interact(local=locals())
            ret=False # I guess?

        return ret

    def process_ep(self, ep):
        # set youtube to public
        # set richard state to live

        if ep.released:

            ret = True  # if something breaks, this will turn false

            # don't make public if there is no host_url (youtube)
            if ep.public_url and ep.host_url and ep.show.client.richard_id:
                ret = ret and self.up_richard(ep)
                if self.options.verbose: print("Richard public.")

            if ep.host_url and ep.show.client.youtube_id:
                ret = ret and self.up_youtube(ep)
                if self.options.verbose: print("Youtube public.")
        else:

            ret = False # Nope. Not until it is both approved and Released.


        return ret

if __name__ == '__main__':
    p=mk_public()
    p.main()

