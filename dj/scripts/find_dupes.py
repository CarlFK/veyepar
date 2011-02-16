#!/usr/bin/python

from collections import defaultdict
from urllib2 import urlopen
from lxml import etree

import json

account = "linuxconfau"

url = 'http://%s.blip.tv/posts/?pagelen=2000&skin=api' % (account)
# print 'http://%s.blip.tv/posts/?pagelen=2000&skin=json' % (account)
# &skin=json

# url_handle = urlopen(url)
#tree = etree.parse(url_handle)
# xml = url_handle.read()
# open('%s.xml' % (account), 'w').write(xml)
xml = open('%s.xml' % (account))
tree = etree.parse(xml)

# eps = tree.xpath('/response/payload/asset')
# e = eps[0]
# print e.xpath('./id/text()')
# print e.xpath('./title/text()')

"""
eps = [ {'id': e.xpath('./id/text()')[0], 
          'title': e.xpath('./title/text()')[0] }
  for e in tree.xpath('/response/payload/asset') ]
# print eps[:3]
"""

d = defaultdict(list)
for ep in tree.xpath('/response/payload/asset'):
  item_id = ep.xpath('./item_id/text()')[0] 
  title = ep.xpath('./title/text()')[0]
  d[title].append(item_id)
    
# print d


veyepar_url = "http://131.181.58.3/main/C/lca/S/lca2011.json"
url_handle = urlopen(veyepar_url)
veyepar_json = url_handle.read()
open('%s.json' % (account), 'w').write(veyepar_json)
veyepar_json = open('%s.json' % (account))
eps = json.load(veyepar_json)
# print eps

names = dict( [ (ep['fields']['name'],ep['fields']) for ep in eps ] ) 
targets = dict( [ (ep['fields']['target'],ep['fields']) for ep in eps ] ) 

for k in d:
    v=d[k]
    if len(v)>1:
        print k
        print "veypar has http://blip.tv/file/%s" % (names[k]['target'])
        for blip_id in v:
            if blip_id != names[k]['target']:
                print "http://blip.tv/file/delete/%s" % (blip_id)





