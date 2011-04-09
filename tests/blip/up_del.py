#!/usr/bin/python

# posts 2 files to blip.tv, then tries (fails) to deletes 1


import xml.etree.ElementTree
import random

import sys
sys.path.append('../../dj/scripts')
import blip_uploader
import pw


def up(filename, blip_id=''):
    """
    upload the passed filename.
    if blip_id is passed, add the file to the existing blip episode
    else create a new episode.
    """

    blip_cli=blip_uploader.Blip_CLI()
    blip_cli.debug = False

    meta = { 'title': 'delete test', 'description': '' }
    files = [['', 'Master', filename], ['1', 'Web', filename]]
    blip_user = pw.blip.keys()[0]
    blip_pw = pw.blip[blip_user]

    response_obj = blip_cli.Upload(
            blip_id, blip_user, blip_pw, files, meta )

    response_xml = response_obj.read()
    tree = xml.etree.ElementTree.fromstring(response_xml)
    response = tree.find('response')
    post_url=response.find('post_url')
    blip_id=post_url.text.split('/')[-1]

    return blip_id

def pick_one(episode_id):
    """
    pick a random file from the passed episode.
    """

    blip_cli=blip_uploader.Blip_CLI()
    blip_cli.debug = False

    xml_code = blip_cli.Get_VideoMeta(episode_id)
    blip_meta = blip_cli.Parse_VideoMeta(xml_code)

    ogvs = []
    for content in blip_meta['contents']:
        url = content['url']
        if content['type'] == 'video/ogg':
            ogvs.append(url)
        
    r = random.randint(0,len(ogvs)-1)
    ogv=ogvs[r]
    return ogv

def del_from_blip(episode_id,file_url):
    print
    print "http://blip.tv/file/%s" % (episode_id)
    print file_url
    return

if __name__ == '__main__':
    
    # upload 
    filename = "Test_Episode.ogv"
    episode_id = '4998133'
    episode_id = up(filename,episode_id)
    # print "episode_id:", episode_id

    # get name of a file to delete
    del_me = pick_one(episode_id)
    # print "del_me:", del_me

    del_from_blip(episode_id,del_me)





