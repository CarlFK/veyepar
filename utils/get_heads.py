# get first meg of a list of files in a playlist
# used to grab a sample of each video 

# get the first few min of each of the files in 
# curl "http://veyepar.nextdayvideo.com/main/pub_play/?client=fosdem&show=fosdem_2014&loc=H1302_Depage&date=2014-02-01" -o playlist.m3u

# kinda like this:
# curl --range -10000 --location http://video.fosdem.org/2014/H1302_Depage/Saturday/Reproducible_Builds_for_Debian.webm  

import optparse
import requests
from urlparse import urlparse
import os

def get_one(url, bytes):

    print url.__repr__()

    # make file name from url
    o = urlparse(url)
    name = o.path.split('/')[-1]
    base,ext = os.path.splitext(name)
    file_name = "%s-head%s" % (base,ext)
    print base,

    session = requests.session()
    headers = {"Range":"bytes=0-%s" % (bytes-1,)}

    return

    response = session.get( url, headers=headers, stream=False)
    print "status:", response.status_code

    open(file_name,'wb').write(response.content)

def one_playlist(f):
    urls = [line.strip() for line in f]
    for url in urls:
        if url:
            # print url
            get_one(url,1000000)

def get_playlist(url):

    print url
    session = requests.session()
    response = session.get( url, )
    playlist = response.text.split('\n')
    one_playlist( playlist )

def parse_args():
    parser = optparse.OptionParser()
    options, args = parser.parse_args()
    return options,args

if __name__ == "__main__":
    options,args = parse_args()

    # get_one("http://video.fosdem.org/2014/H1302_Depage/Saturday/Reproducible_Builds_for_Debian.webm", 1000000)
    # one_playlist( open("playlist.m3u"))
    get_playlist( args[0] )

