#!/usr/bin/python

"""
posts files to blip.tv, then tries (fails) to deletes 1
"""
# to run this:
# create pw.py: blip={'username':'password'}
# put Test_Episode.ogv in the cwd
# handy place to get a small ogv good for uploading:
# cp /home/carl/Videos/veyepar/test_client/test_show/ogv/Test_Episode.ogv .


import xml.etree.ElementTree
import random

import sys
sys.path.append('../../dj/scripts')
import blip_uploader
import pw


def up(blip_user,blip_pw, filename, blip_id=''):
    """
    upload the passed filename.
    if blip_id is passed, add the file to the existing blip episode
    else create a new episode.
    """

    blip_cli=blip_uploader.Blip_CLI()
    blip_cli.debug = False

    meta = { 'title': 'delete test', 'description': '' }
    files = [['', 'Master', filename], ['1', 'Web', filename]]

    response_obj = blip_cli.Upload(
            blip_id, blip_user, blip_pw, files, meta )

    response_xml = response_obj.read()
    tree = xml.etree.ElementTree.fromstring(response_xml)
    response = tree.find('response')
    post_url=response.find('post_url')
    blip_id=post_url.text.split('/')[-1]

    return blip_id

def get_uid(episode_id):

    blip_cli=blip_uploader.Blip_CLI()
    blip_cli.debug = False

    m = blip_cli.Get_VideoMeta(episode_id)
    rss=xml.dom.minidom.parseString(m)

    node=rss.getElementsByTagName("blip:userid")
    user_id = blip_cli.Get_TextFromDomNode(node[0])

    node=rss.getElementsByTagName("blip:posts_id")
    posts_id = blip_cli.Get_TextFromDomNode(node[0])

    return (user_id,posts_id)


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

def get_file_id(user_id, user_name, password, episode_id, file_url):

    blip_cli=blip_uploader.Blip_CLI()
    blip_cli.debug = False

    mm = blip_cli.Get_MoreMeta(user_id,user_name,password,episode_id)
    pm = blip_cli.Parse_MoreMeta(mm)
    ams = pm['posts'][0]['additionalMedia']

    for am in pm['posts'][0]['additionalMedia']:
        if am['url'] == file_url:
            id = am['id']

    return id


def del_from_blip( episode_id,mystery_id,file_url,file_id,
        user_id,user_name,password):
    print
    print "http://blip.tv/file/%s" % (episode_id)
    print "http://blip.tv/dashboard/episode/%s" % (mystery_id)
    print file_url
    print "file id:", file_id
    return

if __name__ == '__main__':
    
    blip_user = pw.blip.keys()[0]
    blip_pw = pw.blip[blip_user]

    # upload 
    filename = "Test_Episode.ogv"
    # blank to create new episode, like if you delete this one
    episode_id = ''
    # episode_id = '4998133'
    episode_id = up(blip_user,blip_pw,filename,episode_id)

    # print "episode_id:", episode_id

    # get the blip user_id (int, not the login name string)
    # and some posts_id that is like a 2nd episode id.
    # user_id = '613931'
    # mystery_id='5015967'
    user_id,mystery_id = get_uid(episode_id)

    # get name of a file to delete
    del_me = pick_one(episode_id)
    # print "del_me:", del_me

    file_id = get_file_id(user_id, blip_user, blip_pw, mystery_id, del_me)

    del_from_blip(episode_id,mystery_id,del_me,file_id, 
            user_id, blip_user, blip_pw)





