# youtube_uploader.py 
# youtbe specific code

# caled from post_yt.py 
# which someday will be jsut post.py with a yt parameter.

# http://code.google.com/apis/youtube/1.0/developers_guide_python.html
# http://code.google.com/apis/youtube/2.0/reference.html

import gdata.youtube
import gdata.youtube.service

from goog_auth_pw import pw

class Uploader(object):

    # input attributes:
    files = []
    thumb = ''
    meta = {}
    upload_user = ''
    old_url = ''
    user=''
    private=False

    # return attributes:
    ret_text = ''
    new_url = ''

    def auth(self):
         
        yt_service = gdata.youtube.service.YouTubeService()

        print pw
        yt_service.email = pw['email']
        yt_service.password = pw['password']
        yt_service.source = 'video eyebaal review'
        yt_service.developer_key = pw["dev_key"]
        yt_service.client_id = "ndv"

        yt_service.ProgrammaticLogin()

        return yt_service
       
if __name__ == '__main__':
    u = Uploader()
    ret = u.auth()

    # import code
    # code.interact(local=locals())
    # import pdb
    # pdb.set_trace()
