# goog_auth.py
# tests authinticating to google

# http://code.google.com/apis/youtube/1.0/developers_guide_python.html
# http://code.google.com/apis/youtube/2.0/reference.html

import gdata.youtube.service

from goog_auth_pw import pw
if __name__ == '__main__':

    yt_service = gdata.youtube.service.YouTubeService()

    yt_service.email = pw['email']
    yt_service.password = pw['password']

    yt_service.ProgrammaticLogin()

    print yt_service
   
    """
    What sucess looks like:
(veyepar)carl@dc10:~/src/veyepar/tests/you_tube$ python goog_auth.py 
<gdata.youtube.service.YouTubeService object at 0x1079ed0>

    What fial looks like:
Traceback (most recent call last):
  File "goog_auth.py", line 47, in <module>
    ret = u.auth()
  File "goog_auth.py", line 41, in auth
    yt_service.ProgrammaticLogin()
  File "/home/carl/goog_auth_test/local/lib/python2.7/site-packages/gdata/service.py", line 793, in ProgrammaticLogin
    raise BadAuthentication, 'Incorrect username or password'
gdata.service.BadAuthentication: Incorrect username or password

    """

    # import code
    # code.interact(local=locals())
    # import pdb
    # pdb.set_trace()
