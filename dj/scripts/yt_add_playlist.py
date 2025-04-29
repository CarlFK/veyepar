#!/usr/bin/python

from process import process

import youtube_v3_uploader

import pw

from django.conf import settings
from main.models import Show, Location, Episode, Raw_File, Cut_List

class mk_public(process):

    ready_state = None

    def up_youtube(self, ep):

        uploader = youtube_v3_uploader.Uploader()

        uploader.client_secrets_file = settings.GOOG_CLIENT_SECRET
        uploader.token_file = settings.SECRETS_DIR / "youtube" / pw.yt[ep.show.client.youtube_id]['filename']

        playlist_id = ep.show.youtube_playlist_id
        if self.options.verbose: print("Setting Youtube playlist")
        try:
            if playlist_id:
                ret = uploader.add_to_playlist(ep.host_url, playlist_id)
        # except apiclient.errors.HttpError as e:
        except youtube_v3_uploader.HttpError as e:
            print(e)
            # this shouldn't happen, prolly debugging something.
            import code
            code.interact(local=locals())

        return ret

    def process_ep(self, ep):
        # set youtube to public
        # set richard state to live

        if ep.released:

            ret = True  # if something breaks, this will turn false

            # don't add to playlist if there is no host_url (youtube)

            if ep.host_url and ep.show.client.youtube_id:
                ret = ret and self.up_youtube(ep)
        else:

            ret = False # Nope. Not until it is both approved and Released.


        return ret

if __name__ == '__main__':
    p=mk_public()
    p.main()

