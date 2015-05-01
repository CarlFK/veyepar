import xml.etree.ElementTree
import copy

import pprint

params = {
        'title_img': '/home/carl/Videos/veyepar/dot_net_fringe/dot_net_fringe_2015/titles/On_the_fringe_of_Nodejs_and_NET_with_Edgejs.png',
        'foot_img': 'bling/fosdem_2014_foot.png',
        'clips':[
            {'filename':'/home/carl/Videos/veyepar/dot_net_fringe/dot_net_fringe_2015/dv/main_stage/2015-04-14/09_02_51.dv',}
            ]
        }

tree=xml.etree.ElementTree.parse('template.mlt')

nodes={}
for id in [
        'pl_title_img', 'tl_title',
        'pl_foot_img', 'tl_foot',
        'pl_vid0', 'tl_vid1',
        'audio_fade_in', 'audio_fade_out',
        'title_fade','foot_fade',
        ]:

    # nodes[id] = copy.deepcopy(tree.find(".//*[@id='{}']".format(id)))
    nodes[id] = tree.find(".//*[@id='{}']".format(id))

mlt = tree.find('.')
play_list = tree.find("./playlist[@id='main bin']")
nodes['pe'] = play_list.find("./entry[@sample]")
for pe in play_list.findall("./entry[@sample]"):
    producer = pe.get('producer')
    producer_node = tree.find("./producer[@id='{}']".format(producer))
    print( producer )
    play_list.remove(pe)
    mlt.remove(producer_node)

print("adding...")

for i in "ABC":

    node_id = "pl_vid{}".format(i)
    print(node_id)

    pe = copy.deepcopy( nodes['pe'] )
    pe.set("producer", node_id)
    play_list.insert(0,pe)

    pi = copy.deepcopy( nodes['pl_vid0'] )
    pi.set("id", node_id)
    mlt.insert(0,pi)

print("checking...")

for pe in play_list.findall("./entry[@sample]"):
    producer = pe.get('producer')
    print(producer)

def set_text(node_id,prop_name,param_id):
    print(node_id,prop_name,param_id)
    p = nodes[node_id].find("property[@name='{}']".format(prop_name))
    p.text = params[param_id]

# set title screen image
set_text('pl_title_img','resource','title_img')
set_text('tl_title','resource','title_img')

set_text('pl_foot_img','resource','foot_img')
set_text('tl_foot','resource','foot_img')


tree.write('output.mlt')

import code; code.interact(local=locals())

"""
pl = tree[1]['main bin']
for pi in pl.findall("entry[@sample]"): 
    print( pi.tag, pi.get('producer') )
    tree[0].remove(pi)

"""

