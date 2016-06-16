# mk_mlt.py 
# Makes a .mlt file
# uses template.mlt which was created using ShotCut GUI NLE


import xml.etree.ElementTree
import copy

import pprint


def mk_mlt(template, output, params):

    def set_text(node,prop_name,value=None):
        # print(node,prop_name,value)
        p = node.find("property[@name='{}']".format(prop_name))
        if value is None:
            node.remove(p)
        else:
            if type(value)==int:
                value = "0:{}.0".format(value)
            elif type(value)==float:
                value = "0:{}".format(value)
            p.text = value

    def set_attrib(node, attrib_name, value=None):
        if value is None:
            del node.attrib[attrib_name]
        else:
            if type(value)==int:
                value = "0:{}.0".format(value)
            # print(attrib_name, value)
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
        'pic_in_pic', 'opacity',
        'channelcopy', 
        'mono', 
        'normalize', 
        'title_fade','foot_fade',
        ]:

        node = tree.find(".//*[@id='{}']".format(id))
        # print(id,node)
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
        # print( producer )
        play_list.remove(pe)
        mlt.remove(producer_node)

    # <playlist id="playlist0">
    # <entry producer="tl_vid1" in="00:00:00.667" out="00:00:03.003" sample="1" /> 
    time_line = tree.find("./playlist[@id='playlist0']")
    for te in time_line.findall("./entry[@sample]"):
        # print("te",te)
        producer = te.get('producer')
        producer_node = tree.find("./producer[@id='{}']".format(producer))
        # print( "producer", producer )
        time_line.remove(te)
        mlt.remove(producer_node)

    nodes['ti_vid2'].remove(nodes['channelcopy'])
    nodes['ti_vid2'].remove(nodes['mono'])
    nodes['ti_vid2'].remove(nodes['normalize'])

    # add each clip to the playlist
    for i,clip in enumerate(params['clips']):

        node_id = "pi_vid{}".format(clip['id'])
        # print("node_id",node_id)

        # setup and add Play List
        pl = copy.deepcopy( nodes['pl_vid0'] )
        pl.set("id", "pl_vid{}".format(clip['id']))
        pl.set("producer", node_id)
        set_attrib(pl, "in", clip['in'])
        set_attrib(pl, "out", clip['out'])
        play_list.insert(i,pl)

        # setup and add Playlist Item
        pi = copy.deepcopy( nodes['pi_vid0'] )
        pi.set("id", node_id)
        set_attrib(pi, "in", clip['in'])
        set_attrib(pi, "out", clip['out'])
        set_text(pi,'length')
        set_text(pi,'resource',clip['filename'])
        mlt.insert(i,pi)

    # add each cut to the timeline
    total_length = 0
    for i,cut in enumerate(params['cuts']):
        # print(i,cut)

        node_id = "ti_vid{}".format(cut['id'])

        tl = copy.deepcopy( nodes['tl_vid2'] )
        tl.set("producer", node_id)
        set_attrib(tl, "in", cut['in'])
        set_attrib(tl, "out", cut['out'])
        time_line.insert(i,tl)

        ti = copy.deepcopy( nodes['ti_vid2'] )
        ti.set("id", node_id)
        set_attrib(ti, "in")
        set_attrib(ti, "out")
        set_text(ti,'length')
        set_text(ti,'resource',cut['filename'])
        set_text(ti,'video_delay',cut['video_delay'])

        # apply the filters to te cuts

        if cut['channelcopy']=='00':
            pass
        elif cut['channelcopy']=='m':
            ti.insert(0,nodes['mono'])
        else:
            channelcopy = copy.deepcopy( nodes['channelcopy'] )
            set_text(channelcopy,'from' , cut['channelcopy'][0])
            set_text(channelcopy,'to' , cut['channelcopy'][1])
            ti.insert(0,channelcopy)

        if cut['normalize']!='0':
            normalize = copy.deepcopy( nodes['normalize'] )
            set_text(normalize,'program' , cut['normalize'])
            ti.insert(0,normalize)

        if nodes['pic_in_pic'] is not None:
            # for Node 15
            ti.insert(0,nodes['pic_in_pic'])
            ti.insert(0,nodes['opacity'])

        if i==0:
            # apply audio fade in/out to first/last cut
            ti.insert(0,nodes['audio_fade_in'])

        mlt.insert(i*2,ti)

        total_length += cut['length']
        print( total_length )

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
    nodes['spacer'].set("length","0:{}.0".format(total_length-8.0))

    # put the 1.5 fadeout at the end
    nodes['audio_fade_out'].set("in","0:{}.0".format(total_length-1.5))

    tree.write(output)
    # import code; code.interact(local=locals())

    return True

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
                'channelcopy':'01',
                'normalize':'-12.0',
                'video_delay':'0.0',
                },], 
        }

    mk_mlt("template.mlt", "test.mlt",  params)
    return 

    params = {
        'title_img': '/home/carl/Videos/veyepar/test_client/test_show/titles/Lets_make_a_Test.png',
        'foot_img': 'bling/ndv-169.png',
        'clips':[],
        'cuts':[], 
        }

    for i in range(5):
        filename = "00_00_{:02}.dv".format(i*3)
        clip = {'id':str(i),
                'filename':'/home/carl/Videos/veyepar/test_client/test_show/dv/test_loc/2010-05-21/{}'.format(filename),
                'length':2,
                'in':None,
                'out':None,
                }

        if i==0: 
            clip['in']=1

        params['clips'].append(clip)

        if i in [1,2,3]:
            params['cuts'].append(
               {'id':str(i),
                'filename':'/home/carl/Videos/veyepar/test_client/test_show/dv/test_loc/2010-05-21/{}'.format(filename),
                'in':None,
                'out':None,
                'length':3,
                'channelcopy':'01',
                'normalize':'-12.0',
                'video_delay':'0.0',
                })


    mk_mlt("template.mlt", "test.mlt",  params)


if __name__ == '__main__':
    test()
