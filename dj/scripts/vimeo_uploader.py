#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Marc Poulhiès
#
# Python module for Vimeo
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Plopifier.  If not, see <http://www.gnu.org/licenses/>.


"""
This is an upload script for Vimeo using its v2 API
"""


import vimeo
import vimeo.config
import vimeo.convenience

import time

import pw 

class Uploader(object):

    # input attributes:
    files = []
    meta = {}
    user=''

    debug_mode=False

    def auth(self, creds):

        client = vimeo.VimeoClient(
                  key=creds['client_id'],
                  secret=creds["client_secret"],
                  token=creds["access"],
                  token_secret=creds["access_secret"],
                  format="json")
        return client

    def upload(self):
   
        client = self.auth(pw.vimeo[self.user])

        quota = client.vimeo_videos_upload_getQuota()
        t = client.vimeo_videos_upload_getTicket()
        vup = vimeo.convenience.VimeoUploader(client, t, quota=quota)
        
        vup.upload(self.files[0]['pathname'])

        vc = vup.complete()
        self.vc = vc
        vid = vc['video_id']
        self.vid = vid
        self.new_url = "http://vimeo.com/%s" % vid

        if self.debug_mode:
            print vid
            import code
            code.interact(local=locals())


    ## use a sleep to wait a few secs for vimeo servers to be synced.
    ## sometimes, going too fast
        time.sleep(5)

        # client.vimeo_videos_setTitle(self.meta['title'], vid)
        # client.vimeo_videos_setDescription(self.meta['description'], vid)

        """
        if options.privacy :
            pusers = []
            ppwd = None
            ppriv = options.privacy
            if options.privacy.startswith("users"):
                pusers = options.privacy.split(":")[1].split(',')
                ppriv = "users"
            if options.privacy.startswith("password"):
                ppwd = options.privacy.split(":")[1]
                ppriv = "password"

            client.vimeo_videos_setPrivacy(ppriv, vid,
                                           users=pusers, password=ppwd)
        """

        return True

if __name__ == '__main__':

    u = Uploader()
    u.user='continuum'
    u.files = ['test.mp4']
    u.meta = {
      'title': "test title",
      'description': "test description",
    }
    u.debug_mode = True

    u.upload()

    print u.url


