#!/usr/bin/python

# push encoded files to data center box
# uses rsync. 

import os, subprocess

from process import process

from main.models import Show, Location, Episode

class push(process):

    ready_state = 3

    def process_ep(self, ep):
        if self.options.verbose: print ep.id, ep.name

        # get a list of video files to upload
        files = []
        for ext in self.options.upload_formats:
            src_pathname = os.path.join( self.show_dir, ext, "%s.%s"%(ep.slug,ext))
            files.append({'ext':ext,'pathname':src_pathname})
      
        # dest_host = 'veyepar@nextdayvideo.com'
        # dest_path = "/home/veyepar/Videos/veyepar/enthought/scipy_2012/mp4"
        for f in files:

            user="veyepar"
            host =  'nextdayvideo.com'
            dest_host = '%s@%s' % (user,host)
            dest_path = "/home/%s/Videos/veyepar/%s/%s/%s" % (
                    user, 
                    ep.show.client.slug, ep.show.slug,
                    f['ext'] )

            dest = "%s:%s" %( dest_host, dest_path )

            cmd = ['rsync',  '-rtvP', '-e', 'ssh -p 222', 
                    f['pathname'], dest ] 
            if self.options.verbose: print cmd
            if self.options.test:
                print "testing, not coppying, returing False"
                ret = False
            else:
"""
sending incremental file list
rsync: change_dir#3 "/home/veyepar/Videos/veyepar/chipy/chipy_aug_2012" failed: No such file or directory (2)
rsync error: errors selecting input/output files, dirs (code 3) at main.c(632) [receiver=3.0.3]
rsync: connection unexpectedly closed (9 bytes received so far) [sender]
rsync error: error in rsync protocol data stream (code 12) at io.c(601) [sender=3.0.8]
ret: 12
"""
# So I guess 12 means "target dir does't exist"

                p = subprocess.Popen( cmd )
                ret = p.wait()
                if self.options.verbose: print "ret:", ret

        # tring to fix the db timeout problem
        # ep=Episode.objects.get(pk=ep.id)
        try:
            ep.save()
        except DatabaseError, e:
            from django.db import connection
            connection.connection.close()
            connection.connection = None
            ep.save()

        return ret

if __name__ == '__main__':
    p=push()
    p.main()

