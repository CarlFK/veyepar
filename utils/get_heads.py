# get first meg of a list of files in a playlist
# used to grab a sample of each video 

# get the first few min of each of the files in 
# curl "http://veyepar.nextdayvideo.com/main/pub_play/?client=fosdem&show=fosdem_2014&loc=H1302_Depage&date=2014-02-01" -o playlist.m3u

# kinda like this:
# curl --range -10000 --location http://video.fosdem.org/2014/H1302_Depage/Saturday/Reproducible_Builds_for_Debian.webm  

import requests
from urlparse import urlparse
import os

def get_one(url, bytes):

    print url

    # make file name from url
    o = urlparse(url)
    name = o.path.split('/')[-1]
    base,ext = os.path.splitext(name)
    file_name = "%s-head%s" % (base,ext)
    print base,

    session = requests.session()
    headers = {"Range":"bytes=0-%s" % (bytes-1,)}

    response = session.get( url, headers=headers, stream=True)
    print "status:", response.status_code

    open(file_name,'wb').write(response.content)

def one_playlist(file_name):
    # urls = open(file_name).read().split('\n')
    urls = [line.strip() for line in open(file_name).readlines()]
    return urls


if __name__ == "__main__":
    # get_one("http://video.fosdem.org/2014/H1302_Depage/Saturday/Reproducible_Builds_for_Debian.webm", 1000000)
    urls = one_playlist("playlist.m3u")
    for url in urls:
        get_one(url,1000000)

