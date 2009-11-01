#!/usr/bin/python

"""
Demo of xml manipulation as used by enc.py to alter the title.svg and cutlist.mlt (both are xml files.)

"""

import xml.etree.ElementTree
from pprint import pprint

mlt="""
<mlt>

  <producer id="title" resource="title.png" in="0" out="149" />
  <producer id="rawvid" resource="/home/juser/vid/t2.dv" />

  <playlist id="playlist0">
    <entry id="clip" producer="rawvid" in="500" out="690" />
    <filter mlt_service="channelcopy" from="1" to="0" />
    <filter mlt_service="volume" max_gain="30" normalise="28" />
  </playlist>

  <playlist id="playlist1">
    <entry producer="title"/>
  </playlist>

  <tractor id="tractor0">
       <multitrack>
         <track producer="playlist0"/>
         <track producer="playlist1"/>
       </multitrack>
       <transition 
         mlt_service="luma" in="100" out="149" a_track="1" b_track="0"/>
   </tractor>

</mlt>
"""

tree = xml.etree.ElementTree.fromstring(mlt)

# There are 2 producer (input) nodes, find them and print their attributes:
producers=tree.findall('producer')
print( "producers:" )
for producer in producers:
    pprint( producer.attrib )

# find the one whos id is 'rawvid'
# Make a list of id's, get the index of 'rawvid', use that on the list of nodes:
ids=[p.attrib['id'] for p in producers]
rawfile_index = ids.index('rawvid')
rawfile_node = producers[rawfile_index]
print( "rawfile_node resource: %s" % rawfile_node.attrib['resource'] )

# set it to some filename:
rawfile_node.attrib['resource'] = 'foo.dv'

# make another producer node:
new_node=xml.etree.ElementTree.Element('producer', {'resource': 'bar.dv'} )
# add it after the rawfile_node:
# this means get a list of top level nodes, 
#  get the rawfile_node index in that list,
#  insert after that:
nodes = tree.findall('*')
position=nodes.index(rawfile_node)
print("rawfile_node position in tree %s" % position )
tree.insert(position+1,new_node)

# replace the playlist entry with 2 new ones.
playlists=tree.findall('playlist')
# get playlist0 in fewer steps by making a dictionary of id:node
d=dict( [(p.attrib['id'],p) for p in playlists] )
pprint( d )
playlist = d['playlist0']

# get the playlist entry (there is only one, so it is the first)
entry = playlist.find('entry')
# delete it from the playlist
playlist.remove(entry)

new_node=xml.etree.ElementTree.Element('entry', {'in':'10', 'out':'20'} )
playlist.insert(0,new_node)
new_node=xml.etree.ElementTree.Element('entry', {'in':'30', 'out':'40'} )
# posision 1 because 0 will put it before the one we just added, which would be odd.
playlist.insert(1,new_node)

print xml.etree.ElementTree.tostring(tree)

#############
# do it again, only using XMLID, wich relies on id attributes being unique across the whole xml file.
# in this case, tree is (tree,{dic of id:node})

tree = xml.etree.ElementTree.XMLID(mlt)

# get the dv file node
dvfile=tree[1]['rawvid']

# make another
new_node=xml.etree.ElementTree.Element('producer', {'resource': 'bar.dv'} )

#same code to find the posision:
nodes = tree[0].findall('*')
position=nodes.index(dvfile)
tree[0].insert(position+1,new_node)

# remove the original
tree[0].remove(dvfile)

# replace the playlist entry with 2 new ones
clips = [(1,'500','690'),(2,'1000','999999')]
# get the clip placeholder, the playlist and remove the clip from the playlist
clip=tree[1]['clip']
playlist=tree[1]['playlist0']
playlist.remove(clip)

for id,start,end in clips:
    clip.attrib['id']="clip%s"%id
    clip.attrib['in']=start
    clip.attrib['out']=end
    new=xml.etree.ElementTree.Element('entry', clip.attrib )
    playlist.insert(0,new)

xml.etree.ElementTree.dump(tree[0])


