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
  <producer id="footer" resource="footer.png" in="0" out="0" /> 

  <playlist id="playlist0">
    <entry producer="title"/>
  </playlist>

  <playlist id="playlist1">
    <entry id="clip" producer="producer0" in="500" out="690" />

   <filter in="0" out="30" id="fadein">
    <property name="track">0</property>
    <property name="window">75</property>
    <property name="max_gain">20dB</property>
    <property name="mlt_type">filter</property>
    <property name="mlt_service">volume</property>
    <property name="tag">volume</property>
    <property name="gain">0</property>
    <property name="end">1</property>
   </filter>

   <filter in="58" out="87" id="fadeout">
    <property name="track">0</property>
    <property name="window">75</property>
    <property name="max_gain">20dB</property>
    <property name="mlt_type">filter</property>
    <property name="mlt_service">volume</property>
    <property name="tag">volume</property>
    <property name="gain">1</property>
    <property name="end">0</property>
   </filter>

    <entry id="foot0" producer="footer"/>
  </playlist>

  <playlist id="playlist2">
    <entry id="foot1" producer="footer"/>
  </playlist>

  <tractor id="tractor0">
    <multitrack>
      <track id="track2" producer="playlist2"/>
      <track id="track1" producer="playlist1"/>
      <track id="track0" producer="playlist0"/>
    </multitrack>
    <transition id="transition0"
      mlt_service="luma" in="100" out="149" a_track="2" b_track="1"/>
    <transition id="transition1"
      mlt_service="luma" in="0" out="0" a_track="1" b_track="0"/>

  <transition in="0" out="0" id="transition0">
   <property name="a_track">1</property>
   <property name="b_track">2</property>
   <property name="mlt_type">transition</property>
   <property name="mlt_service">mix</property>
   <property name="always_active">1</property>
   <property name="combine">1</property>
   <property name="internal_added">237</property>
  </transition>

  </tractor>

</mlt>
"""

# overlay ndv log to obscure sensitive information 
# that leaked into presentation opps.
"""
    <filter id="filter0" in="51139" out="51197">
      <property name="track">1</property>
      <property name="factory">loader</property>
      <property name="resource">ndv.png</property>
      <property name="mlt_type">filter</property>
      <property name="mlt_service">watermark</property>
      <property name="composite.geometry">58%,93%,100%,100%</property>
      <property name="composite.progressive">1</property>
    </filter>
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
            'presentertitle': "",
            'date': episode.start.strftime("%B %d, %Y"),
        }
 
    svg_in=open(source).read()
    tree=xml.etree.ElementTree.XMLID(svg_in)

    for key in text:
        if self.options.verbose: print key
        # tollerate template where tokens have been removed
        if tree[1].has_key(key):
            if self.options.verbose: 
                print "org", tree[1][key].text
                # print "new", text[key].encode()
            tree[1][key].text=text[key]

    if tree[1].has_key('presenternames'):
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


  def mkmlt(self,title_img,credits_img,episode,cls,rfs):
        """
        assemble a mlt playlist from:
        mlt template, title screen image, 
        filter parameters (currently just audio) 
        and cutlist+raw filenames
        """

        # output file name
        # this gets used twice: 
        # once to get melt to scan the files and count total frames of content
        # then the trailer gets added to the xml
        # and a final version gets written out.  whacky.
        mlt_pathname = os.path.join(self.work_dir,"%s.mlt"%episode.slug)

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
            dvfile.attrib['id']="producer%s"%rf.id
            if self.options.load_temp:
                src_pathname = os.path.join(self.episode_dir,rf.filename)
                dst_path = os.path.join(
                  self.tmp_dir,episode.slug,os.path.dirname(rf.filename))
                rawpathname = os.path.join(
                  self.tmp_dir,episode.slug,rf.filename.replace(':','_'))
                cmds = [['mkdir', '-p', dst_path],
                        ['rsync', '--progress', '--size-only',  
                            src_pathname, rawpathname]]
                self.run_cmds(episode,cmds)
            else:
                if rf.filename.startswith('\\'):
                    rawpathname = rf.filename
                else:
                    rawpathname = os.path.join(self.episode_dir,rf.filename)
            dvfile.attrib['resource']=rawpathname
            new=xml.etree.ElementTree.Element('producer', dvfile.attrib )
            tree[0].insert(pos,new)
            pos+=1

# set credits file
        footer=tree[1]['footer']
        footer.attrib['resource']=credits_img


# get the dv clip placeholder, remove it from the playlist
        clip=tree[1]['clip']
        playlist=tree[1]['playlist1']
        playlist.remove(clip)

# add in the clips
        pos = 1
        for cl in cls:
          print cl
          if cl.raw_file.duration:
            print "duration:", cl.raw_file.duration
            clip.attrib['id']="clip%s"%cl.id
            clip.attrib['producer']="producer%s"%cl.raw_file.id
          
            # set start/end on the clips if they are set in the db
            # else remove them, 
            # ignoroe the error if they are not there to remove

            if cl.start:
                in_frame=time2f(cl.start,self.fps)
		clip.attrib['in']=str(in_frame)
            else:
                try:
                    del( clip.attrib['in'] )
                except KeyError:
                    pass

            if cl.end:
                out_frame=time2f(cl.end,self.fps) 
                clip.attrib['out']=str(out_frame)
            else:
                try:
                    del( clip.attrib['out'] )
                except KeyError:
                    pass

            # add the new clip to the tree
            print clip.attrib
            new=xml.etree.ElementTree.Element('entry', clip.attrib )
            playlist.insert(pos,new)
            pos+=1

        # write out the xml we have so far
        # then pass it to melt to calc total frames
        mlt_xml = xml.etree.ElementTree.tostring(tree[0])
        open(mlt_pathname,'w').write(mlt_xml)
        p = subprocess.Popen( ['melt', mlt_pathname, 
           '-consumer', 'xml'], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        out,err = p.communicate()

        # hack to remove "Plugin 1046 exists in both ...."
        # out = '\n'.join(
        #        l for l in out.split('\n') if not l.startswith('Plugin') )

        t=xml.etree.ElementTree.XMLID(out)
        frames=t[1]['tractor1'].get('out')
        frames=int(frames)

        # fade in/out the audio of the main track
        # in is already set: 0-30 frames.
        # out needs to be set to last 30 frames
        fadeout = tree[1]['fadeout']
        fadeout.set("in",str(frames-30))
        fadeout.set("out",str(frames))

        # set 2 parts of the footer:
        # 1. 3 seconds of fade from video to footer
        # 2. append 3 seconds of footer

        x1,end,x3=str(frames-90),str(frames),str(frames+90)

        # 1.
        transition = tree[1]['transition1']
        transition.set('in',x1)
        transition.set('out',end)

        track = tree[1]['track2']
        track.set('in',x1)
        track.set('out',end)

        pf = tree[1]['foot1']
        pf.set('in',x1)
        pf.set('out',end)

        # 2. 
        pf = tree[1]['footer']
        pf.set('out',"90")

        pf = tree[1]['foot0']
        pf.set('in',str(end))
        pf.set('out',str(x3))

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
            # or m/'mono' to kick in this hack
            if episode.channelcopy=='m':
                new=xml.etree.ElementTree.Element('filter', 
                    {'mlt_service':'mono', 'channels':'2'} )
            else:
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
            # like the title and transistion from title to cut
            tree[0].remove(title)
            x=tree[1]['playlist0']
            # print x
            tree[0].remove(x)
            x=tree[1]['tractor0']
            tree[0].remove(x)

        if self.options.verbose: xml.etree.ElementTree.dump(tree[0])

        mlt_xml = xml.etree.ElementTree.tostring(tree[0])
        open(mlt_pathname,'w').write(mlt_xml)

        if self.options.debug_log:
            mlt_xml = mlt_xml.replace('<','&lt;').replace('>','&gt;')
            mlt_xml = mlt_xml.replace('&','&amp;')
            episode.description += "\n%s\n" % (mlt_xml)
            episode.save()

        return mlt_pathname

  def enc_all(self, mlt_pathname, episode):

        def enc_one(ext):
              out_pathname = os.path.join(
                self.show_dir, ext, "%s.%s"%(episode.slug,ext))

              # cmds=["melt -verbose -progress -profile square_%s %s -consumer avformat:%s acodec=%s ab=128k ar=44100 vcodec=%s minrate=0 b=900k progressive=1" % ( self.options.dv_format, mlt_pathname, out_pathname, acodec, vcodec)]
              if ext=='webm': 
                  cmds=["/usr/bin/melt"   "/tmp/kde-carl/kdenliveY27808.mlt -profile dv_ntsc -consumer avformat:/home/carl/kdenlive/untitled.webm progress=1 acodec=libvorbis ab=128k ar=44100 vcodec=libvpx minrate=0 b=600k aspect=@4/3 maxrate=1800k g=120 qmax=42 qmin=10 threads=2"% (fix_me)]
              if ext=='flv': 
                  cmds=["melt -progress -profile square_%s %s -consumer avformat:%s progressive=1 acodec=libfaac ab=96k ar=44100 vcodec=libx264 b=110k vpre=/usr/share/ffmpeg/libx264-hq.ffpreset" % ( self.options.dv_format, mlt_pathname, out_pathname,)]
              if ext=='flac': 
                  # 16kHz/mono 
                  cmds=["melt -verbose -progress %s -consumer avformat:%s ar=16000" % ( mlt_pathname, out_pathname)]
              if ext=='mp3': 
                  cmds=["melt -verbose -progress %s -consumer avformat:%s" % ( mlt_pathname, out_pathname)]

              if ext=='mp4':
                  # High Quality Master 720x480 NTSC
                  tmp_pathname = os.path.join(
                      self.tmp_dir,"%s.%s"%(episode.slug,ext))
                  ffpreset=open('/usr/share/ffmpeg/libx264-hq.ffpreset').read().split('\n')
                  ffpreset = [i for i in ffpreset if i]
                  cmd="melt -progress -profile square_%s %s -consumer avformat:%s deinterlace=bob threads=%s aspect=@4/3 progressive=1 acodec=libmp3lame ar=48000 ab=256k vcodec=libx264 b=1024k" % ( self.options.dv_format, mlt_pathname, tmp_pathname, self.options.threads, )
                  # acodec=libfaac
                  # cmd="melt -progress -profile square_%s %s -consumer avformat:%s aspect=@4/3 progressive=1 acodec=libfaac ar=48000 ab=256k vcodec=libx264 b=1024k" % ( self.options.dv_format, mlt_pathname, tmp_pathname, )
                  cmd = cmd.split()
                  cmd.extend(ffpreset)
                  cmds=[cmd]
                  cmds.append( ["qt-faststart", tmp_pathname, out_pathname] )
                  # cmds.append( ["mv", tmp_pathname, '/tmp'] )
                  if self.options.rm_temp:
                      cmds.append( ["rm", tmp_pathname] )

              if ext=='m4v': 
                  # iPhone
                  tmp_pathname = os.path.join( 
                      self.tmp_dir,"%s.%s"%(episode.slug,ext))
                  # combine settings from 2 files
                  ffpreset=open('/usr/share/ffmpeg/libx264-default.ffpreset').read().split('\n')
                  ffpreset.extend(open('/usr/share/ffmpeg/libx264-ipod640.ffpreset').read().split('\n'))
                  ffpreset = [i for i in ffpreset if i]
                  cmd="melt -progress -profile square_%s %s -consumer avformat:%s s=432x320 aspect=@4/3 progressive=1 acodec=libfaac ar=44100 ab=128k vcodec=libx264 b=70k" % ( self.options.dv_format, mlt_pathname, tmp_pathname, )
                  cmd = cmd.split()
                  cmd.extend(ffpreset)
                  cmds=[cmd]
                  cmds.append( ["qt-faststart", tmp_pathname, out_pathname] )
                  # cmds.append( ["mv", tmp_pathname, '/tmp'] )
                  if self.options.rm_temp:
                      cmds.append( ["rm", tmp_pathname] )
              if ext=='dv': 
                  out_pathname = os.path.join( 
                      self.tmp_dir,"%s.%s"%(episode.slug,ext))
                  cmds=["melt -verbose -progress %s -consumer avformat:%s pix_fmt=yuv411p progressive=1" % ( mlt_pathname, out_pathname)]
              if ext=='ogv': 
                  # melt/ffmpeg ogv encoder is loopy, 
                  # so make a .dv and pass it to ffmpeg2theora
                  ret = enc_one("dv")
                  if ret:
                      dv_pathname = os.path.join( 
                          self.tmp_dir,"%s.dv"%(episode.slug))
                      cmds=["ffmpeg2theora --videoquality 5 -V 600 --audioquality 5 --channels 1 %s -o %s" % (dv_pathname, out_pathname)]
                      if self.options.rm_temp:
                          cmds.append( ["rm", dv_pathname] )
                  else:
                      return ret

              ret = self.run_cmds(episode, cmds)
              if ret and not os.path.exists(out_pathname) \
                     and not self.options.test:
                   print "melt returned %ret, but no output: %s" % \
                       ( ret, out_pathname )
                   ret=False

              return ret


        def one_format(ext, acodec=None, vcodec=None):
            """
            check the passed format against the list of formats to encode
            if it is on the list, encode that format.
            """
            if self.options.verbose: 
                print "checking %s in [%s]" % (ext,self.options.upload_formats)
            if ext in self.options.upload_formats:
                # ret = enc_one(ext, acodec, vcodec)
                ret = enc_one(ext)
            else:
                # this is the case where we don't do this format, 
                # so don't flag as error
                ret = True

            return ret


        ret = True
        # ret = ret and one_format("ogg", "vorbis", "libtheora")
        ret = ret and one_format("flv")
        # ret = ret and one_format("flv", "libmp3lame", "flv")
        ret = ret and one_format("mp4")
        ret = ret and one_format("mp3")
        ret = ret and one_format("flac")
        ret = ret and one_format("m4v")
        ret = ret and one_format("dv")
        ret = ret and one_format("ogv")

        return ret

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
        svg_name = episode.show.client.title_svg \
                if episode.show.client.title_svg \
                else "title.svg"

        template = os.path.join(self.show_dir, "bling", svg_name)
        title_base = os.path.join(self.show_dir, "bling", episode.slug)
        title_img=self.mktitle(template, title_base, episode)

# define credits
        credits_img = episode.show.client.credits \
                   if episode.show.client.credits \
                   else 'ndv1-black.png'
        credits_img = os.path.join(self.show_dir, "bling", credits_img)

# get list of raw footage for this episode
        rfs = Raw_File.objects. \
            filter(cut_list__episode=episode,cut_list__apply=True).\
            exclude(trash=True).distinct()

# make a .mlt file for this episode
        mlt = self.mkmlt(title_img,credits_img,episode,cls,rfs)

# do the final encoding:
# using melt
        ret = self.enc_all(mlt, episode)

        if self.options.enc_script:
            cmd = [self.options.enc_script, 
                    self.show_dir, episode.slug]
            ret = ret and self.run_cmds(episode,[cmd])

        if self.options.load_temp and self.options.rm_temp:
            cmds=[]
            for rf in rfs:
                dst_path = os.path.join(self.tmp_dir,episode.slug,os.path.dirname(rf.filename))
                rawpathname = os.path.join(self.tmp_dir,episode.slug,rf.filename)
                cmds.append( ['rm', rawpathname] )
            cmds.append( ['rmdir', dst_path] )
            dst_path = os.path.join(self.tmp_dir,episode.slug)
            cmds.append( ['rmdir', dst_path] )
            self.run_cmds(episode,cmds)

    else:
        print "No cutlist found."

    return ret


  def add_more_options(self, parser):
        parser.add_option('--enc-script', 
          help='encode shell script' )
        parser.add_option('--load-temp', action="store_true", 
          help='copy .dv to temp files' )
        parser.add_option('--rm-temp', 
          help='remove large temp files' )
        parser.add_option('--threads')

  def add_more_option_defaults(self, parser):
        parser.set_defaults(threads=2)

if __name__ == '__main__':
    p=enc()
    p.main()

