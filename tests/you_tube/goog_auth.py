# goog_auth.py
# tests authinticating to google

import gdata.youtube.service

from goog_auth_pw import pw
if __name__ == '__main__':

    yt_service = gdata.youtube.service.YouTubeService()

    yt_service.email = pw['email']
    yt_service.password = pw['password']

    yt_service.ProgrammaticLogin()

    print yt_service
   
