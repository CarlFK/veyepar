#!/usr/bin/python

# push encoded files to data center box
# uses rsync. 

import os, subprocess

from process import process
from main.models import Show, Location, Episode

class push(process):

    ready_state = 3
    ret = None

    def process_ep(self, ep):
        return True

        # get a list of video files to upload
        files = []
        for ext in self.options.upload_formats:
            src_pathname = os.path.join( self.show_dir, ext, "%s.%s"%(ep.slug,ext))
            files.append({'ext':ext,'pathname':src_pathname})
      
        # dest_host = 'veyepar@nextdayvideo.com'
        # dest_path = "/home/veyepar/Videos/veyepar/enthought/scipy_2012/mp4"
        for f in files:

            # Ryans data center box, 
            # veyepar user and /home dir
            user="veyepar"
            host =  'nextdayvideo.com'
            dest_host = '%s@%s' % (user,host)
            dest_path = "/home/%s/Videos/veyepar/%s/%s/%s" % (
                    user, 
                    ep.show.client.slug, ep.show.slug,
                    f['ext'] )

            dest = "%s:%s" %( dest_host, dest_path )

            # 'ssh -p 222' = use ssh on port 222

            cmd = ['rsync',  '-rtvP', '-e', 'ssh -p 222', 
                    f['pathname'], dest ] 

            ret = self.run_cmd(cmd)

            self.ret = ret ## for test runner

            # rync errors we should contend with
            # 12 = "target dir does't exist" ??
            # man rsync says 12=Error in rsync protocol data stream
            """
sending incremental file list
rsync: change_dir#3 "/home/veyepar/Videos/veyepar/chipy/chipy_aug_2012" failed: No such file or directory (2)
rsync error: errors selecting input/output files, dirs (code 3) at main.c(632) [receiver=3.0.3]
rsync: connection unexpectedly closed (9 bytes received so far) [sender]
rsync error: error in rsync protocol data stream (code 12) at io.c(601) [sender=3.0.8]
ret: 12
"""

        # tring to fix the db timeout problem
        # this is bad - it steps on the current values im memory:
        # ep=Episode.objects.get(pk=ep.id)
        # this seems to work:
        try:
            ep.save()
        except DatabaseError as e:
            from django.db import connection
            connection.connection.close()
            connection.connection = None
            ep.save()

        return ret

if __name__ == '__main__':
    p=push()
    p.main()

