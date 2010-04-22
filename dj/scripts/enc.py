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


def time2s(time):
    """ given 's.s' or 'h:m:s.s' returns s.s """
    if ':' in time:
        sec = reduce(lambda x, i: x*60 + i, 
            map(float, time.split(':')))  
    else:
        # print time, len(time), [c for c in time]
        sec = float(time)
    return sec

def time2f(time,fps):
    if time[-1]=='f':
        return int(time[:-1])
    else:
        return int(time2s(time)*fps)

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
 
  def run_cmd(self,cmd):
    """
    given command list
    if verbose prints stuff,
    runs it, returns pass/fail.
    """
    if self.options.verbose:
        print cmd
        print ' '.join(cmd)

    p=subprocess.Popen(cmd)
    p.wait()
    retcode=p.returncode
    if retcode:
        if self.options.verbose:
            print "command failed"
            print retcode
        ret = False
    else:
        ret = True
    return ret

  def run_cmds(self, episode, cmds):
      """
      given a list of commands
      append them to the episode's shell script
      then run each
      abort and return False if any fail.
      """
      
      # script goes in show's tmp dir
      script_pathname = os.path.join(
          self.show_dir, "tmp", episode.slug+".sh")
      sh = open(script_pathname,'a')

      for cmd in cmds: 
          if type(cmd)==list:
              sh.writelines(' '.join(cmd))
          else:
              sh.writelines(cmd)
              cmd=cmd.split()
          sh.write('\n')
          if not self.run_cmd(cmd):
              return False

      sh.write('\n')
      sh.close()

      return True
 
  def mktitle(self, source, output_base, episode):
    """
    Make a title slide by filling in a pre-made svg with name/authors.
    melt uses librsvg which doesn't support flow, 
    wich is needed for long titles, so render it to a .png using inkscape
    """
    text={
            'client': episode.show.client.name, 
            'show': episode.show.name, 
            'title': episode.name, 
            'authors': episode.authors,
        }
 
    svg_in=open(source).read()
    tree=xml.etree.ElementTree.XMLID(svg_in)
    # print tree[1]
    # tree[1]['title'].text=name
    # for key in ['client', 'title']:

    for key,value in text:
        # tollerate template where tokens have been removed
        if tree[1].has_key(key):
            tree[1][key].text=value

    if text['authors']:
        prefix = "Featuring" if "," in text['authors'] else "By"
        tree[1]['presenternames'].text="%s %s" % (prefix,text['authors'])
    else:
        # remove the text (there is a placholder to make editing sane)
        tree[1]['presenternames'].text=""


    cooked_svg_name='%s.svg'%output_base
    open(cooked_svg_name,'w').write(xml.etree.ElementTree.tostring(tree[0]))
    png_name="%s.png"%output_base
    if self.options.verbose: print png_name
    cmd=["inkscape", cooked_svg_name, "--export-png", png_name]
    self.run_cmds(episode,[cmd])

    return png_name


  def mkmlt(self,title_img,episode,cls,rfs):
        """
        assemble a mlt playlist from:
        mlt template, title screen image, 
        filter parameters (currently just audio) 
        and cutlist+raw filenames
        """

# parse the xml into a tree of nodes
        tree= xml.etree.ElementTree.XMLID(mlt)

# set the title to the title slide we just made
        title=tree[1]['title']
        title.attrib['resource']=title_img


# get the dvfile placeholder and remove it from the tree
        dvfile=tree[1]['producer0']
        tree[0].remove(dvfile)

# add in the dv files
        pos = 1
        for rf in rfs:
          print rf
          if rf.duration():
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

# get the clip placeholder, the playlist and remove the clip from the playlist
        clip=tree[1]['clip']
        playlist=tree[1]['playlist0']
        playlist.remove(clip)

# add in the clips
        pos = 0
        for cl in cls:
          print cl
          if cl.raw_file.duration():
            clip.attrib['id']="clip%s"%cl.id
            clip.attrib['producer']="producer%s"%cl.raw_file.id

            in_frame=time2f(cl.start,self.fps) if cl.start else 0
            out_frame=time2f(cl.end,self.fps) if cl.end else 999999

            # end not needed anymore 
            # (as of 2/9/10, will take out 9999 once melt version bumps)

            clip.attrib['in']=str(in_frame)
            clip.attrib['out']=str(out_frame)

            new=xml.etree.ElementTree.Element('entry', clip.attrib )
            playlist.insert(pos,new)
            pos+=1

# add volume tweeks
            """
    <filter mlt_service="channelcopy" from="1" to="0" />
    <filter mlt_service="volume" max_gain="30" normalise="28" />
                {'mlt_service':'volume', 
                'max_gain':'20', 
                'limiter':'20',
                'normalise':self.options.normalise} )
            """
        normalise = episode.normalise or '-12db'
        if self.options.upload_formats=='flac': normalise=''
        if normalise and normalise!='0':
            if self.options.verbose: print "normalise:", normalise
            new=xml.etree.ElementTree.Element('filter', 
                {'mlt_service':'volume', 
                'normalise':normalise} )
            playlist.insert(pos,new)

        if episode.channelcopy:
            if self.options.verbose: print 'channelcopy:', episode.channelcopy
            # channelcopy should be 01 or 10.
            fro,to=list(episode.channelcopy)
            new=xml.etree.ElementTree.Element('filter', 
                {'mlt_service':'channelcopy', 
                'from':fro, 'to':to} )
            playlist.insert(pos,new)

        if self.options.upload_formats=='flac': 
            # mix channels to mono
            new=xml.etree.ElementTree.Element('filter', 
                {'mlt_service':'mono', 'channels':'2'} )
            # this should be 1, but 
            # "service=mono channels=1" lowers pitch
            # https://sourceforge.net/tracker/?func=detail&aid=2972735
            playlist.insert(pos,new)

            # super hack: remove a bunch of stuff that messes up flac
            tree[0].remove(title)
            x=tree[1]['playlist1']
            print x
            tree[0].remove(x)
            x=tree[1]['tractor0']
            tree[0].remove(x)

        if self.options.verbose: xml.etree.ElementTree.dump(tree[0])

        mlt_pathname = os.path.join(self.show_dir, "tmp", "%s.mlt"%episode.slug)
        open(mlt_pathname,'w').write(xml.etree.ElementTree.tostring(tree[0]))

        return mlt_pathname

  def mk_title_dv(self, mlt_pathname, episode):

        # make an intro .dv from title and audio
        cmd="melt -verbose -profile %s %s in=0 out=149 -consumer avformat:%s pix_fmt=yuv411p" 
        dv_pathname = os.path.join(
            self.show_dir, "tmp", "%s_title.dv"%episode.slug)
        cmd = cmd % ( self.options.format.lower(), mlt_pathname, dv_pathname)
        ret = self.run_cmds(episode,[cmd])
        # if not ret: raise something
        return dv_pathname

  def run_melt(self, mlt_pathname, episode):
        def one_format(ext, acodec=None, vcodec=None):
            if self.options.verbose: 
                print "checking %s in [%s]" % (ext,self.options.upload_formats)

            if ext in self.options.upload_formats:
              out_pathname = os.path.join(
                self.show_dir, ext, "%s.%s"%(episode.slug,ext))

              cmds=["melt -verbose -progress -profile %s %s -consumer avformat:%s acodec=%s ab=128k ar=44100 vcodec=%s minrate=0 b=900k progressive=1" % ( self.options.format.lower(), mlt_pathname, out_pathname, acodec, vcodec)]
              if ext=='flac': 
                  # 16kHz/mono 
                  cmds=["melt -verbose -progress %s -consumer avformat:%s ar=16000" % ( mlt_pathname, out_pathname)]
              if ext=='mp3': 
                  cmds=["melt -verbose -progress %s -consumer avformat:%s" % ( mlt_pathname, out_pathname)]
              if ext=='m4v': 
                  tmp_pathname = os.path.join(
                      self.show_dir, "tmp", "%s.%s"%(episode.slug,ext))
                  # out_pathname = '/tmp/%s.%s' %(episode.slug,ext)
                  # acodec=aac or libfaac
                  cmds=["melt -progress -profile %s %s -consumer avformat:%s s=432x320 aspect=@4/3 progressive=1 acodec=libfaac ar=44100 ab=128k vcodec=libx264 b=700k vpre=/usr/share/ffmpeg/libx264-ipod640.ffpreset" % ( self.options.format.lower(), mlt_pathname, tmp_pathname, )]
                  cmds.append( ["qt-faststart", tmp_pathname, out_pathname] )
              if ext=='dv': 
                  out_pathname = '/tmp/%s.%s' %(episode.slug,ext)
                  cmds=["melt -verbose -progress -profile %s %s -consumer avformat:%s pix_fmt=yuv411p progressive=1" % ( self.options.format.lower(), mlt_pathname, out_pathname)]
# f=dv pix_fmt=yuv411p s=720x480

              ret = self.run_cmds(episode, cmds)
              if ret:
                  if not os.path.exists(out_pathname):
                      print "melt returned 0, but no output: %s" % out_pathname
                      ret=False

              return ret
            # this is the case where we don't do this format, 
            # so don't flag as error
            return True

        ret = True
        ret = ret and one_format("ogg", "vorbis", "libtheora")
        ret = ret and one_format("flv", "libmp3lame", "flv")
        ret = ret and one_format("mp4", "libmp3lame", "mpeg4")
        ret = ret and one_format("mp3")
        ret = ret and one_format("flac")
        ret = ret and one_format("m4v")
        ret = ret and one_format("dv")

        return ret

  def mkdv(self, mlt_pathname, episode, cls ):
        """
        assemble parts into a master .dv file
        so that something like ffmpeg2theora can encode it.
        it is different from run_melt-one_format("dv") because it does not 
        re-encode - it just copies chunks of files.
        """
        title_dv=self.mk_title_dv(mlt_pathname, episode)

        # make a new dv file using just the frames to encode
        dv_pathname = os.path.join(self.show_dir,
            "tmp",episode.slug+".dv")
        if self.options.verbose: 
            print "making %s - may take awhile..." % dv_pathname
        outf=open(dv_pathname,'wb')

        # splice in the intro dv make by melt()
        title=open(title_dv,'rb').read()
        title_bytes=len(title)
        outf.write(title)

        for c in cls:
            if self.options.verbose: 
                print (c.raw_file.filename, c.start,c.end)
            raw_pathname = os.path.join(self.episode_dir,c.raw_file.filename)
            inf=open(raw_pathname,'rb')
            inf.seek(time2b(c.start,self.fps,self.bpf,0)+title_bytes)
            # there is a problem if the first clip is shorter than the title.
# the next clip will start at 0, 
# which is part of the title, so it will play twice.  oh well.
# it also does't pick up the volume adjustments. 
            title_bytes=0 
            size=os.fstat(inf.fileno()).st_size
            end = time2b(c.end,self.fps,self.bpf,size)
            while inf.tell()<end:
                outf.write(inf.read(self.bpf))
            inf.close()
        outf.close()
    
        return dv_pathname


  def dv2theora(self,episode,dvpathname,cls,rfs):
        """
        transcode dv to ogv
        """
        oggpathname = os.path.join(self.show_dir, "ogv", "%s.ogv"%episode.slug)
        # cmd="ffmpeg2theora --videoquality 5 -V 600 --audioquality 5 --speedlevel 0 --optimize --keyint 256 --channels 1".split()
        cmd="ffmpeg2theora --videoquality 5 -V 600 --audioquality 5 --keyint 256 --channels 1".split()
        cmd+=['--output',oggpathname]
        cmd+=[dvpathname]
        return cmd

# this code is useless
        if len(cls)==1:
            # use the raw dv file and ffmpeg2theora params to trim
            # Not much point in this now that the title side gets made
            # because now there is never the case of one .dv file
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

# make a title slide
        template = os.path.join(self.show_dir, "bling", "title.svg")
        title_base = os.path.join(self.show_dir, "bling", episode.slug)
        title_img=self.mktitle(template, title_base, episode)

# get list of raw footage for this episode
        rfs = Raw_File.objects.filter(
            cut_list__episode=episode).exclude(trash=True).distinct()

# make a .mlt file for this episode
        mlt = self.mkmlt(title_img,episode,cls,rfs)

# do the final encoding:
# using melt
        ret = self.run_melt(mlt, episode)
  
# using ogv requires dv, so roll that in
        if "ogv" in self.options.upload_formats:
            
            if "dv" in self.options.upload_formats:
                # use the dv created with melt
                # which is now in /tmp/
                # dvpathname = os.path.join(
                #     self.show_dir, "dv", "%s.dv"%episode.slug )
                dvpathname = '/tmp/'+episode.slug+'.dv'
            else:
                # create the dv (mktitle+copy frames)
                dvpathname = self.mkdv(mlt,episode,cls)
 
            oggpathname = os.path.join(
                self.show_dir, "ogv", "%s.ogv"%episode.slug)
            cmd="ffmpeg2theora --videoquality 5 -V 600 --audioquality 5" \
                " --channels 1".split()
            cmd+=[dvpathname,'--output',oggpathname]
            ret = ret and self.run_cmds(episode, [cmd])

            # delete /tmp/foo.dv 
            os.remove(dvpathname)

        if "m4v" in self.options.upload_formats:
            ext="m4v"
            # tmp_pathname = '/tmp/%s.%s' % (episode.slug,ext)
            tmp_pathname = os.path.join(
                self.show_dir, "tmp", "%s.%s"%(episode.slug,ext))
            # delete /tmp/foo.m4v 
            os.remove(tmp_pathname)

        if self.options.enc_script:
            cmd = [self.options.enc_script, 
                    self.show_dir, episode.slug]
            ret = ret and self.run_cmds(episode,[cmd])


    else:
        print "No cutlist found."

    return ret


  def add_more_options(self, parser):
        parser.add_option('--enc_script', 
          help='encode shell script' )

if __name__ == '__main__':
    p=enc()
    p.main()

