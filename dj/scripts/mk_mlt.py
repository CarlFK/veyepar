# mk_mlt.py 
# Makes a .mlt file
# uses template.mlt which was created using ShotCut GUI NLE


import xml.etree.ElementTree
import copy

import pprint


def mk_mlt(template, output, params):

    def set_text(node,prop_name,value=None):
        print(node,prop_name,value)
        p = node.find("property[@name='{}']".format(prop_name))
        if value is None:
            node.remove(p)
        else:
            if type(value)==int:
                value = "0:{}.0".format(value)
            p.text = value

    def set_attrib(node, attrib_name, value=None):
        if value is None:
            del node.attrib[attrib_name]
        else:
            if type(value)==int:
                value = "0:{}.0".format(value)
            print(attrib_name, value)
            node.set(attrib_name, value)

    # parse the template 
    tree=xml.etree.ElementTree.parse(template)

    # grab nodes we are going to store values into
    nodes={}
    for id in [
        'pi_title_img', 'ti_title',
        'pi_foot_img',  'ti_foot',
        # 'spacer',
        'pl_vid0', 'pi_vid0', # Play List and Item
        'tl_vid2', 'ti_vid2', # Time Line and Item
        'audio_fade_in', 'audio_fade_out',
        'title_fade','foot_fade',
        ]:

        node = tree.find(".//*[@id='{}']".format(id))
        print(id,node)
        nodes[id] = node

    # special case because Shotcut steps on the id='spacer'
    # <playlist id="playlist1">
    # <blank id="spacer" length="00:00:00.267"/>
    nodes['spacer'] = tree.find("./playlist[@id='playlist1']blank")

    # remove all placeholder nodes
    mlt = tree.find('.')

    play_list = tree.find("./playlist[@id='main bin']")
    for pe in play_list.findall("./entry[@sample]"):
        producer = pe.get('producer')
        producer_node = tree.find("./producer[@id='{}']".format(producer))
        print( producer )
        play_list.remove(pe)
        mlt.remove(producer_node)

    # <playlist id="playlist0">
    # <entry producer="tl_vid1" in="00:00:00.667" out="00:00:03.003" sample="1" /> 
    time_line = tree.find("./playlist[@id='playlist0']")
    for te in time_line.findall("./entry[@sample]"):
        print("te",te)
        producer = te.get('producer')
        producer_node = tree.find("./producer[@id='{}']".format(producer))
        print( "producer", producer )
        time_line.remove(te)
        mlt.remove(producer_node)

    # add each clip to the playlist
    for i,clip in enumerate(params['clips']):

        node_id = "pi_vid{}".format(clip['id'])
        print("node_id",node_id)

        # setup and add Play List
        pl = copy.deepcopy( nodes['pl_vid0'] )
        pl.set("id", "pl_vid{}".format(clip['id']))
        pl.set("producer", node_id)
        set_attrib(pl, "in")
        set_attrib(pl, "out")
        play_list.insert(i,pl)

        # setup and add Playlist Item
        pi = copy.deepcopy( nodes['pi_vid0'] )
        pi.set("id", node_id)
        set_attrib(pi, "in")
        set_attrib(pi, "out")
        set_text(pi,'length')
        mlt.insert(i,pi)

        set_text(pi,'resource',clip['filename'])

    # add each cut to the timeline
    # apply audio fade in/out to first/last cut
    first = True
    total_length = 0
    for i,cut in enumerate(params['cuts']):
        print(i,cut)

        node_id = "ti_vid{}".format(cut['id'])

        tl = copy.deepcopy( nodes['tl_vid2'] )
        tl.set("producer", node_id)
        set_attrib(tl, "in", cut['in'])
        set_attrib(tl, "out", cut['out'])
        time_line.insert(i,tl)

        ti = copy.deepcopy( nodes['ti_vid2'] )
        ti.set("id", node_id)
        set_attrib(ti, "in", cut['in'])
        set_attrib(ti, "out", cut['out'])
        set_text(ti,'length' , cut['length'])
        set_text(ti,'resource',cut['filename'])

        if first:
            ti.insert(0,nodes['audio_fade_in'])
            first = False

        mlt.insert(i,ti)

        total_length += cut['length']

    # ti is left over from the above loop
    ti.insert(0,nodes['audio_fade_out'])

    # set title screen image
    set_text(nodes['pi_title_img'],'resource',params['title_img'])
    set_text(nodes['ti_title'],'resource',params['title_img'])

    # set footer image
    set_text(nodes['pi_foot_img'],'resource',params['foot_img'])
    set_text(nodes['ti_foot'],'resource',params['foot_img'])

    # set the lenght of the spacer so it puts the footer image to end-5sec
    # Duration: 27mn 53s
    # nodes['ti_foot'].set("in",str(total_length))
    # nodes['spacer'].set("length","00:27:46.00")
    nodes['spacer'].set("length","0:{}.0".format(total_length-8.8))

    tree.write(output)

    # import code; code.interact(local=locals())

"""
pl = tree[1]['main bin']
for pi in pl.findall("entry[@sample]"): 
    print( pi.tag, pi.get('producer') )
    tree[0].remove(pi)

"""

def test():

    params = {
        'title_img': '/home/carl/Videos/veyepar/dot_net_fringe/dot_net_fringe_2015/titles/On_the_fringe_of_Nodejs_and_NET_with_Edgejs.png',
        'foot_img': 'bling/fosdem_2014_foot.png',
        'clips':[
                {'id':'123',
                'filename':'/home/carl/Videos/veyepar/dot_net_fringe/dot_net_fringe_2015/dv/main_stage/2015-04-14/09_02_51.dv',
                }
            ],
        'cuts':[{'id':'456',
                'filename':'/home/carl/Videos/veyepar/dot_net_fringe/dot_net_fringe_2015/dv/main_stage/2015-04-14/09_02_51.dv',
                'in':None,
                'out':None,
                'length':1673, # Duration: 27mn 53s
                },], 
        'audio_level': None,
        'channel_copy': None,
        }

    # mk_mlt("template.mlt", "test.mlt",  params)
    # return 

    params = {
        'title_img': '/home/carl/Videos/veyepar/test_client/test_show/titles/Lets_make_a_Test.png',
        'foot_img': 'bling/ndv-169.png',
        'clips':[],
        'cuts':[], 
        'audio_level': None,
        'channel_copy': None,
        }

    for i in range(5):
        filename = "00_00_{:02}.dv".format(i*3)
        params['clips'].append(
                {'id':str(i),
                'filename':'/home/carl/Videos/veyepar/test_client/test_show/dv/test_loc/2010-05-21/{}'.format(filename),
                'length':2,
                })
        if i in [1,2,3]:
            params['cuts'].append(
               {'id':str(i),
                'filename':'/home/carl/Videos/veyepar/test_client/test_show/dv/test_loc/2010-05-21/{}'.format(filename),
                'in':None,
                'out':None,
                'length':3,
                })

    mk_mlt("template.mlt", "test.mlt",  params)


if __name__ == '__main__':
    test()
