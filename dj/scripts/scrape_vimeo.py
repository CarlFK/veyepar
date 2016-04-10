# scrape_vimeo.py
# grabs the list of vids on vimeo, 
# shoves them into veyepar
# because I accedently blanked them all out

import json
import requests

from steve.util import html_to_markdown

from . import process  # not using process, but this sets up some stuff.
from main.models import Episode

def get_page(url):

    session = requests.session()
    response = session.get(url)
    page = response.json
    return page

def main():

    vs = get_page("http://vimeo.com/api/v2/pydata/videos.json?page=1")
    vs += get_page("http://vimeo.com/api/v2/pydata/videos.json?page=2")
    vs = vs[:35]
    print(len(vs))
    
    for v in vs:
        title = v['title']
        # print title
        es = Episode.objects.filter(show__slug="pydata_sv_2013", name=title)
        if len(es) != 1:
            print(title)
            print(v['url'])
            print()
        else:
            e=es[0]
            e.host_url = v['url']
            e.description = html_to_markdown(v['description'])
            e.save()
 

if __name__ == '__main__':
    main()


