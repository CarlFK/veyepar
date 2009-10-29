#!/usr/bin/python

# encodes to ogg

import os,sys,subprocess
import xml.etree.ElementTree

from process import process

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

mlt="""
<mlt>

  <producer id="title" resource="title.png" in="0" out="149" />
  <producer id="producer0" resource="/home/juser/vid/t2.dv" />

  <playlist id="playlist0">
    <entry id="clip" producer="producer0" in="500" out="690" />
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

def run_cmd(cmd):
    print cmd
    cmd = cmd.split()
    print cmd
    p=subprocess.Popen(cmd)
    p.wait()
    retcode=p.returncode
    return retcode


def time2s(time):
    """ given 's.s' or 'h:m:s.s' returns s.s """
    if ':' in time:
        sec = reduce(lambda x, i: x*60 + i, 
            map(float, time.split(':')))  
    else:
        print time, len(time), [c for c in time]
        sec = float(time)
    return sec

def time2f(time,fps):
    if time[-1]=='f':
        return int(time[:-1])
    else:
        return time2s(time)*fps

def time2b(time,fps,bpf,default):
    """
    converts the time stored in the db 
      (as blank, seconds,  h:m:s.s )
    to the byte offset in the file.
    blank returns default, typically either 0 or filesize for start/end.
    fps is 25.0 for pal and 29.9 ntsc.
    bpf (bytes per frame) is 120000 for both.
    """
    if time:
        bytes = int(time2s(time)*fps)*bpf
    else:
        bytes = default
    return bytes

class enc(process):

  ready_state = 2
  
  def mktitle(self, source, output_base, text):
    """
    Make a title slide by filling in a pre-made svg with name/authors.
    melt uses librsvg which doesn't support flow, 
    wich is needed for long titles, so render it to a .png using inkscape
    text is {'client':'PyCon', 'show':'', title, authors
    """

    svg_in=open(source).read()
    tree=xml.etree.ElementTree.XMLID(svg_in)
    # print tree[1]
    # tree[1]['title'].text=name
    for key in ['client', 'show', 'title']:
        tree[1][key].text=text[key]

    prefix = "Featuring" if "," in text['authors'] else "By"
    tree[1]['presenternames'].text="%s %s" % (prefix,text['authors'])

    cooked_svg_name='%s.svg'%output_base
    open(cooked_svg_name,'w').write(xml.etree.ElementTree.tostring(tree[0]))
    png_name="%s.png"%output_base
    if self.options.verbose: print png_name
    cmd="inkscape %s --export-png %s" % (cooked_svg_name, png_name)
    run_cmd(cmd)

    # dv_name="%s.dv"%output_base
    # cmd="melt %s %s" % (png_name,dv_name)

    return png_name


  def melt(self,episode,cls,rfs):
        """
        assemble a mlt playlist, create a title screen, 
        call melt to mix title with playlist
        currenly just do the first few seconds that are related to the title
        let something else encode the rest
        """

# parse the xml into a tree of nodes
        tree= xml.etree.ElementTree.XMLID(mlt)
# make a title slide
        template = os.path.join(self.show_dir, "bling", "title.svg")
        title_base = os.path.join(self.show_dir, "tmp", episode.slug)
        text={
            'client': episode.location.show.client.name, 
            'show': episode.location.show.name, 
            'title': episode.name, 
            'authors': episode.authors,
        }
        title_name=self.mktitle(template, title_base, text)

# set the title to the title slide we just made
        title=tree[1]['title']
        title.attrib['resource']=title_name


# get the dvfile placeholder and remove it from the tree
        dvfile=tree[1]['producer0']
        tree[0].remove(dvfile)

# add in the dv files
        pos = 1
        for rf in rfs:
            print rf
            dvfile.attrib['id']="producer%s"%rf.id
# hack to use .ogg instead of .dv
            # rawpathname = os.path.join(self.episode_dir,rf.basename()+".ogg")
# unhack to use .dv            
            rawpathname = os.path.join(self.episode_dir,rf.filename)

            dvfile.attrib['resource']=rawpathname
            # new=xml.etree.ElementTree.SubElement(tree[0],'producer', dvfile.attrib )
            new=xml.etree.ElementTree.Element('producer', dvfile.attrib )
            tree[0].insert(pos,new)
            pos+=1


        xml.etree.ElementTree.dump(tree[0])
        print tree[1]

# get the clip placeholder, the playlist and remove the clip from the playlist
        clip=tree[1]['clip']
        playlist=tree[1]['playlist0']
        playlist.remove(clip)

# add in the clips
        pos = 0
        # for id,start,end in [(1,'500','690'),(2,'1000',None)]:
        for cl in cls:
            print cl
            clip.attrib['id']="clip%s"%cl.id
            clip.attrib['producer']="producer%s"%cl.raw_file.id
            clip.attrib['in']=str(time2f(cl.start,self.fps)) if cl.start else '0'
            clip.attrib['out']=str(time2f(cl.end,self.fps)) if cl.end else '999999'
            new=xml.etree.ElementTree.Element('entry', clip.attrib )
            playlist.insert(pos,new)
            pos+=1

# add volume tweeks
            """
    <filter mlt_service="channelcopy" from="1" to="0" />
    <filter mlt_service="volume" max_gain="30" normalise="28" />
            """
        if self.options.normalize:
            new=xml.etree.ElementTree.Element('filter', 
                {'mlt_service':'volume', 
                'max_gain':'1', 
                'limiter':'1',
                'normalise':self.options.normalize} )
            playlist.insert(pos,new)

        if self.options.channelcopy:
            # channelcopy should be 01 or 10.
            fro,to=list(self.options.channelcopy)
            new=xml.etree.ElementTree.Element('filter', 
                {'mlt_service':'channelcopy', 
                'from':fro, 'to':to} )
            playlist.insert(pos,new)

        xml.etree.ElementTree.dump(tree[0])

        mlt_pathname = os.path.join(self.show_dir, "tmp", "%s.mlt"%episode.slug)
        open(mlt_pathname,'w').write(xml.etree.ElementTree.tostring(tree[0]))

        # make an intro .dv from title and audio
        cmd="melt -verbose -profile dv_%s %s in=0 out=149 -consumer avformat:%s pix_fmt=yuv411p" 
        # cmd="melt -verbose -profile dv_%s %s in=0 out=149 -consumer avformat:%s f=dv pix_fmt=yuv411p" 
        dv_pathname = os.path.join(self.show_dir, "dv", "%s.dv"%episode.slug)
        ret = run_cmd(cmd% (self.options.format.lower(), mlt_pathname, dv_pathname))
        # ogg_pathname = os.path.join(self.show_dir, "ogg", "%s.ogg"%episode.slug)
        # ret = run_cmd("ffmpeg2theora %s -o %s" % ( dv_pathname, ogg_pathname))


        # full lenght encodings
        def one_format(ext, acodec, vcodec):
            if ext in self.options.output_format:
              cmd="melt -verbose -profile dv_%s %s -consumer avformat:%s acodec=%s ab=128k ar=44100 vcodec=%s minrate=0 b=900k progressive=1 deinterlace_method=onefield" 
              out_pathname = os.path.join(
                self.show_dir, ext, "%s.%s"%(episode.slug,ext))
              cmd = cmd % ( self.options.format.lower(), 
                mlt_pathname, out_pathname, acodec, vcodec)
              ret = run_cmd(cmd)
              return ret

        ret = one_format("ogg", "vorbis", "libtheora")
        ret = one_format("flv", "libmp3lame", "flv")
        ret = one_format("mp4", "libmp3lame", "mpeg4")

        return dv_pathname
        return ret

  def mkdv(self,episode,title_dv,cls,rfs):
        """
        assemble parts into a master .dv file
        """

        # make a new dv file using just the frames to encode
        dvpathname = os.path.join(self.episode_dir,episode.slug+".dv")
        if self.options.verbose: 
            print "making %s - may take awhile..." % dvpathname
        outf=open(dvpathname,'wb')

# hack to splice in the intro dv make by melt()
        inf=open(title_dv,'rb')
        outf.write(inf.read())
        super_hack=150*self.bpf

        for c in cls:
            if self.options.verbose: 
                print (c.raw_file.filename, c.start,c.end)
            rawpathname = os.path.join(self.episode_dir,c.raw_file.filename)
            inf=open(rawpathname,'rb')
            inf.seek(time2b(c.start,29.9,self.bpf,0))
            inf.seek(super_hack)
            super_hack=0
            size=os.fstat(inf.fileno()).st_size
            end = time2b(c.end,29.9,self.bpf,size)
            while inf.tell()<end:
                outf.write(inf.read(self.bpf))
            inf.close()
        outf.close()
    
        return dvpathname


  def dv2theora(self,episode,title_dv,cls,rfs):
        """
        transcode dv ot ogg
        """
        oggpathname = os.path.join(self.show_dir, "ogg", "%s.ogg"%episode.slug)
        cmd="ffmpeg2theora --videoquality 5 -V 600 --audioquality 5 --speedlevel 0 --optimize --keyint 256 --channels 1".split()
        cmd+=['--output',oggpathname]

        if len(cls)==1 and not title_dv:
            # use the raw dv file and ffmpeg2theora params to trim
            c=cls[0]
            if c.start: cmd+=['--starttime',str(time2s(c.start))]
            if c.end: cmd+=['--endtime',str(time2s(c.end))]
            dvpathname = os.path.join(self.episode_dir,c.raw_file.filename)
        else:
            dvpathname = self.mkdv(episode,title_dv,cls,rfs)
                   
        cmd+=[dvpathname]

        return cmd

  def process_ep(self,episode):
    # print episode
    ret = False
    cls = Cut_List.objects.filter(
        episode=episode, apply=True).order_by('sequence')
    # print len(cls), episode.name.__repr__()
    print episode.name
    for cl in cls:
        print cl.start, cl.end

    if cls:
# get list of raw footage for this episode
        rfs = Raw_File.objects.filter(
            cut_list__episode=episode).exclude(trash=True).distinct()
# for now, call melt to create the title part
        title_dv = self.melt(episode,cls,rfs)
# maybe call a script to do the final encoding:
        if self.options.enc_script or "theora" in self.options.output_format:
          # consolidate all the dv files into one  
          dvpathname = self.mkdv(episode,title_dv,cls,rfs)
          if self.options.enc_script:
            # define where the script should put output and temp files
#             out_pathname = os.path.join(
#                 self.show_dir, "mp4", "%s.mp4"%episode.slug)
#             temp_pathname = os.path.join(
#                 self.show_dir, "tmp", "%s.mp4"%episode.slug)
            cmd = [self.options.enc_script, 
                    dvpathname, self.show_dir, episode.slug]

          if "theora" in self.options.output_format:
            cmd = self.dv2theora(episode,title_dv,cls,rfs)

          print ' '.join(cmd)
          p=subprocess.Popen(cmd)
          p.wait()
          retcode=p.returncode

        if not retcode:
            ret = True
        else:
            print episode.id, episode.name
            print "transcode failed"
            print retcode

    else:
        print "No cutlist found."

    return ret


  def add_more_options(self, parser):
        parser.add_option('--output-format', default='',
          help='list of format(s) to output' )
        parser.add_option('--enc_script', 
          help='encode shell script' )
        parser.add_option('--channelcopy', 
          help='copy left to right (10) or right to left (01)' )
        parser.add_option('--normalize', 
          help='normalise audio' )


if __name__ == '__main__':
    p=enc()
    p.main()

