#!/usr/bin/python

"""
assembles raw cuts into final, titles, tweaks audio, encodes to format for upload.
"""
import os
import sys
import subprocess
import xml.etree.ElementTree
# import xml.etree.ElementTree as ET

from mk_mlt import mk_mlt

import pprint
from process import process

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

# http://mltframework.blogspot.com/2012/04/time-properties.html

mlt = """
<mlt>

  <producer id="title" resource="title.png" in="0" out="149" />
  <producer id="producer0" resource="/home/juser/vid/t2.dv" />

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

  </playlist>

  <tractor id="tractor0">
    <multitrack>
      <track id="track1" producer="playlist1"/>
      <track id="track0" producer="playlist0"/>
    </multitrack>
    <transition id="transition0"
      mlt_service="luma" in="100" out="149" a_track="2" b_track="1"/>
    <transition id="transition1"
      mlt_service="luma" in="-90" out="-60" a_track="1" b_track="0"/>

  <transition in="0" out="30" id="transition0">
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
    sec = reduce(lambda x, i: x * 60 + i,
                 map(float, time.split(':')))
    return sec


def time2f(time, fps):
    if time[-1] == 'f':
        return int(time[:-1])
    else:
        return int(time2s(time) * fps)


def time2b(time, fps, bpf, default):
    """
    converts the time stored in the db
      (as blank, seconds,  h:m:s.s )
    to the byte offset in the file.
    blank returns default, typically either 0 or filesize for start/end.
    fps is 25.0 for pal and 29.9 ntsc.
    bpf (bytes per frame) is 120000 for both.
      (huh? doesn't matter, this func not used.)
    """
    if time:
        bytes = int(time2s(time) * fps) * bpf
    else:
        bytes = default
    return bytes


class enc(process):

    ready_state = 2

    def mk_title_svg(self, raw_svg, texts):
        """
        Make a title slide by filling in a pre-made svg with name/authors.
        return: svg
        """
        tree = xml.etree.ElementTree.XMLID(raw_svg)

        for key in texts:
            if self.options.verbose:
                print "looking for:", key
            # tollerate template where tokens have been removed
            if tree[1].has_key(key):

                if key == "license":
                    # CC license image
                    if self.options.verbose:
                        print "found in svg:", tree[1][key]
                        print "replacing with:", texts[key]
                        t = tree[1][key]
                        # import code; code.interact(local=locals())
                    if texts[key] is None:
                        # del(tree[1][key])
                        # print tree[1].has_key(key)
                        tree[1][key].clear()
                    else:
                        t.set('{http://www.w3.org/1999/xlink}href', texts[key])
                else:
                    if self.options.verbose:
                        print "found in svg:", tree[1][key].text
                        print "replacing with:", texts[key]  # .encode()
                    tree[1][key].text = texts[key]

        # cooked_svg = xml.etree.ElementTree.tostring(tree[0])
        # print "testing...", "license" in cooked_svg

        if tree[1].has_key('presenternames'):
            # some people like to add spiffy text near the presenter name(s)
            if texts['authors']:
                # prefix = u"Featuring" if "," in texts['authors'] else "By"
                # tree[1]['presenternames'].text=u"%s %s" % (prefix,texts['authors'])
                tree[1]['presenternames'].text = texts['authors']
            else:
                # remove the text (there is a placholder to make editing sane)
                tree[1]['presenternames'].text = ""

        cooked_svg = xml.etree.ElementTree.tostring(tree[0])
        print "testing...", "license" in cooked_svg

        return cooked_svg

    def get_title_text(self, episode):
        # lets try putting (stuff) on a new line
        title = episode.name
        authors = episode.authors

        if episode.show.slug == 'wtd_na_2015':
            title = title.upper()
            authors = authors.upper()

        if episode.show.slug != 'pygotham_2015' and  len(title) > 80: # crazy long titles need all the lines  
            title2 = ''
        elif ": " in title: # the space keeps 9:00 from breaking
            pos = title.index(":") + 1
            title, title2 = title[:pos], title[pos:].strip()
        elif " - " in title:
            # error if there is more than 1.
            title, title2 = title.split(' - ')
        elif " -- " in title:
            # error if there is more than 1.
            title, title2 = title.split(' -- ')
        elif " (" in title:
            pos = title.index(" (")
            # +1 skip space in " ("
            title, title2 = title[:pos], title[pos + 1:]
        elif " using " in title:
            pos = title.index(" using ")
            title, title2 = title[:pos], title[pos + 1:]
        elif ";" in title:
            pos = title.index(";") + 1
            title, title2 = title[:pos], title[pos:].strip()
        elif "?" in title:
            pos = title.index("?") + 1
            title, title2 = title[:pos], title[pos:].strip()
        else:
            title2 = ""

        if episode.license:
            license = "cc/{}.svg".format(episode.license.lower())
        else:
            license = None

        if episode.tags:
            tags = episode.tags.split(',')
            tag1 = tags[0]
        else:
            tags = []
            tag1 = ''

        """
        if ',' in authors:
            authors = authors.split(', ')
            author2 = ', '.join(authors[1:])
            authors = authors[0].strip()
        else:
            author2 = ''
        """
        author2 = ''

        if episode.show.slug == 'pygotham_2015':
            date = episode.start.strftime("%B %-d, %Y")
        else:
            date = episode.start.strftime("%Y-%m-%-d")

        texts = {
            'client': episode.show.client.name,
            'show': episode.show.name,
            'title': title,
            'title2': title2,
            'tag1': tag1,
            'authors': authors,
            'author2': author2,
            'presentertitle': "",
            'twitter_id': episode.twitter_id,
            'date': date,
            'time': episode.start.strftime("%H:%M"),
            'license': license,
            'room': episode.location.name,
        }

        return texts

    def svg2png(self, svg_name, png_name, episode):
        """
        Make a title slide png file.
        melt uses librsvg which doesn't support flow, 
        wich is needed for long titles, so render it to a .png using inkscape
        """

        # create png file
        # inkscape does not return an error code on failure
        # so clean up previous run and
        # check for the existance of a new png
        if os.path.exists(png_name):
            os.remove(png_name)
        # cmd=["inkscape", svg_name, "--export-png", png_name]
        cmd = ["inkscape", svg_name,
               "--export-png", png_name,
               # "--export-width", "720",
               ]
        ret = self.run_cmds(episode, [cmd])
        ret = os.path.exists(png_name)

        # if self.options.verbose: print cooked_svg
        if self.options.verbose:
            print png_name

        if not ret:
            print "svg:", svg_name
            png_name = None

        return png_name

    def mk_title(self, episode):
        # make a title slide

        # if we find titles/custom/(slug).svg, use that
        # else make one from the tempalte
        custom_svg_name = os.path.join(
            self.show_dir, "titles", "custom", episode.slug + ".svg")
        if self.options.verbose: print "custom:", custom_svg_name
        if os.path.exists(custom_svg_name):
            cooked_svg_name = custom_svg_name
        else:
            svg_name = episode.show.client.title_svg
            print svg_name
            template = os.path.join(
                os.path.split(os.path.abspath(__file__))[0],
                "bling",
                svg_name)
            # happy_filename = episode.slug.encode('utf-8')
            happy_filename = episode.slug
            # happy_filename = ''.join([c for c in happy_filename if c.isalpha()])
            title_base = os.path.join(self.show_dir, "titles", happy_filename)
            raw_svg = open(template).read()
            # tree=xml.etree.ElementTree.XMLID(raw_svg)
            texts = self.get_title_text(episode)
            cooked_svg = self.mk_title_svg(raw_svg, texts)

            # save svg to a file
            # strip 'broken' chars because inkscape can't handle the truth
            # output_base=''.join([ c for c in output_base if c.isalpha()])
            # output_base=''.join([ c for c in output_base if ord(c)<128])
            # output_base=output_base.encode('utf-8','ignore')

            cooked_svg_name = os.path.join(
                self.show_dir, "titles", '%s.svg' % episode.slug)
            open(cooked_svg_name, 'w').write(cooked_svg)

        png_name = os.path.join(
            self.show_dir, "titles", '%s.png' % episode.slug)

        title_img = self.svg2png(cooked_svg_name, png_name, episode)
        # title_img=png_name

        if title_img is None:
            print "missing title png"
            return False

        return title_img

    def mkmlt_1(self, title_img, credits_img, episode, cls, rfs):
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
        mlt_pathname = os.path.join(self.work_dir, "%s.mlt" % episode.slug)

# parse the xml into a tree of nodes
        # mlt_template_name = os.path.join(self.show_dir,"bling/chiweb/chiweb.mlt")
        mlt_template_name = os.path.join(self.show_dir,
                                         os.path.split(
                                             os.path.abspath(__file__))[0],
                                         "bling",
                                         "chiweb/chiweb.mlt")
        # print mlt_template_name
        # mlt = open(mlt_template_name).read()
        # print mlt

        tree = xml.etree.ElementTree.XMLID(mlt)

# set the title to the title slide we just made
        # import code; code.interact(local=locals())

        title = tree[1]['title']
        title.attrib['resource'] = title_img

# get the dvfile placeholder and remove it from the tree
        dvfile = tree[1]['producer0']
        tree[0].remove(dvfile)

# add in the dv files
        pos = 1
        for rf in rfs:
            if self.options.load_temp:
                src_pathname = os.path.join(self.episode_dir, rf.filename)
                dst_path = os.path.join(
                    self.tmp_dir, episode.slug, os.path.dirname(rf.filename))
                rawpathname = os.path.join(
                    self.tmp_dir, episode.slug, rf.filename)
                # self.tmp_dir,episode.slug,rf.filename.replace(':','_'))
                cmds = [['mkdir', '-p', dst_path],
                        ['rsync', '--progress', '--size-only',
                            src_pathname, rawpathname]]
                self.run_cmds(episode, cmds)
            else:
                if rf.filename.startswith('\\'):
                    rawpathname = rf.filename
                else:
                    rawpathname = os.path.join(self.episode_dir, rf.filename)

            # check for missing input file
            # typically due to incorrect fs mount
            if not os.path.exists(rawpathname):
                print "can't find rawpathname", rawpathname
                return False

            dvfile.attrib['id'] = "producer%s" % rf.id
            dvfile.attrib['resource'] = rawpathname
            new = xml.etree.ElementTree.Element('producer', dvfile.attrib)
            tree[0].insert(pos, new)
            pos += 1

# get the dv clip placeholder, remove it from the playlist
        clip = tree[1]['clip']
        playlist = tree[1]['playlist1']
        playlist.remove(clip)

# add in the clips
        pos = 1
        for cl in cls:
            print cl
            if cl.raw_file.duration:
                print "duration:", cl.raw_file.duration
                clip.attrib['id'] = "clip%s" % cl.id
                clip.attrib['producer'] = "producer%s" % cl.raw_file.id

                # set start/end on the clips if they are set in the db
                # else remove them,
                # ignoroe the error if they are not there to remove

                if cl.start:
                    in_frame = time2f(cl.start, self.fps)
                    clip.attrib['in'] = str(in_frame)
                else:
                    try:
                        del(clip.attrib['in'])
                    except KeyError:
                        pass

                if self.options.test:
                    out_frame = "300"
                    clip.attrib['out'] = str(out_frame)
                elif cl.end:
                    out_frame = time2f(cl.end, self.fps)
                    clip.attrib['out'] = str(out_frame)
                else:
                    try:
                        del(clip.attrib['out'])
                    except KeyError:
                        pass

                # add the new clip to the tree
                print clip.attrib
                new = xml.etree.ElementTree.Element('entry', clip.attrib)
                playlist.insert(pos, new)
                pos += 1

        # write out the xml we have so far
        # then pass it to melt to calc total frames

        mlt_xml = xml.etree.ElementTree.tostring(tree[0])
        open(mlt_pathname, 'w').write(mlt_xml)
        p = subprocess.Popen(
            ['melt', mlt_pathname, '-consumer', 'xml'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()

        # hack to remove "Plugin 1046 exists in both ...."
        # out = '\n'.join(
        #        l for l in out.split('\n') if not l.startswith('Plugin') )

        print out
        print "err", err

        t = xml.etree.ElementTree.XMLID(out)
        frames = t[1]['tractor1'].get('out')
        frames = int(frames)

        # fade in/out the audio of the main track
        # in is already set: 0-30 frames.
        # out needs to be set to last 30 frames
        fadeout = tree[1]['fadeout']
        # fadeout.set("in",str(frames-30))
        # fadeout.set("out",str(frames))
        fadeout.set("in", "-120")
        fadeout.set("out", "-90")

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
        if self.options.upload_formats == 'flac':
            normalise = ''
        if normalise and normalise != '0':
            if self.options.verbose:
                print "normalise:", normalise
            new = xml.etree.ElementTree.Element('filter',
                                                {'mlt_service': 'volume',
                                                 'normalise': normalise})
            playlist.insert(pos, new)

        # default defined here:
        # 01 is copy Left to Right
        channelcopy = episode.channelcopy or \
            episode.location.channelcopy or \
            "01"

        if channelcopy:
            if self.options.verbose:
                print 'channelcopy:', channelcopy
            # channelcopy should be 01 or 10.
            # or m/'mono' to kick in this hack
            if channelcopy == 'm':
                new = xml.etree.ElementTree.Element('filter',
                                                    {'mlt_service': 'mono', 'channels': '2'})
            else:
                fro, to = list(channelcopy)
                new = xml.etree.ElementTree.Element('filter',
                                                    {'mlt_service': 'channelcopy',
                                                     'from': fro, 'to': to})
            playlist.insert(pos, new)

        if self.options.upload_formats == 'flac':
            # mix channels to mono
            new = xml.etree.ElementTree.Element('filter',
                                                {'mlt_service': 'mono', 'channels': '2'})
            # this should be 1, but
            # "service=mono channels=1" lowers pitch
            # https://sourceforge.net/tracker/?func=detail&aid=2972735
            playlist.insert(pos, new)

            # super hack: remove a bunch of stuff that messes up flac
            # like the title and transistion from title to cut
            tree[0].remove(title)
            x = tree[1]['playlist0']
            # print x
            tree[0].remove(x)
            x = tree[1]['tractor0']
            tree[0].remove(x)

        if self.options.verbose:
            xml.etree.ElementTree.dump(tree[0])

        mlt_xml = xml.etree.ElementTree.tostring(tree[0])
        open(mlt_pathname, 'w').write(mlt_xml)

        if self.options.debug_log:
            mlt_xml = mlt_xml.replace('<', '&lt;').replace('>', '&gt;')
            mlt_xml = mlt_xml.replace('&', '&amp;')
            episode.description += "\n%s\n" % (mlt_xml,)
            episode.save()

        return mlt_pathname

    def get_params(self, episode, rfs, cls):
        """
        assemble a dict of params to send to mk_mlt
        mlt template, title screen image, 
        filter parameters (currently just audio) 
        and cutlist+raw filenames
        """
        def get_title(episode):
            # if we find titles/custom/(slug).svg, use that
            # else make one from the tempalte
            custom_png_name = os.path.join(
                self.show_dir, "titles", "custom", episode.slug + ".png")
            print "custom:", custom_png_name
            if os.path.exists(custom_png_name):
                title_img = custom_png_name
            else:
                title_img = self.mk_title(episode)

            return title_img

        def get_foot(episode):
            # define credits
            credits_img = episode.show.client.credits \
                if episode.show.client.credits \
                else 'ndv-169.png'

            credits_img = os.path.join(
                os.path.split(os.path.abspath(__file__))[0],
                "bling",
                credits_img)

            if credits_img[-4:] == ".svg":
                # convert to png because melt doesn't do svgs as well
                png_name = credits_img[:-4] + ".png"
                credits_img = self.svg2png(credits_img,  png_name, episode)

            return credits_img

        def get_clips(rfs):

            """
            return list of possible input files
            this may get the files and store them localy.
            start/end segments are under get_cuts.
            ps.  this is not used for encoding,
            just shows in ShotCut for easy dragging onto the timeline.
            """

            clips = []
            for rf in rfs:

                # if rf.filename.startswith('\\'):
                #     rawpathname = rf.filename
                # else:
                rawpathname = os.path.join(
                    self.episode_dir, rf.filename)

                # check for missing input file
                # typically due to incorrect fs mount
                if not os.path.exists(rawpathname):
                    print "can't find rawpathname", rawpathname
                    return False

                clips.append({
                    'id': rf.id,
                    'filename': rawpathname,
                    })

            return clips


        def get_cuts(cls):

            """
            gets the list of cuts.
            input file, start, end, filters
            ps, does not reference the clips above.
            """

            def hms_to_clock(hms):
                """
                Converts what media players show h:m:s
                to the mlt time format h:m:s.s 
                for more on this:
                http://mltframework.blogspot.com/2012/04/time-properties.html
                """
                if not hms:
                    return None

                if ":" not in hms:
                    hms = "0:" + hms

                if "." not in hms:
                    hms = hms + ".0"

                return hms

            cuts = []
            for cl in cls:
                cut = {}

                cut['id'] = cl.id

                rawpathname = os.path.join(
                    self.episode_dir, cl.raw_file.filename)
                cut['filename'] = rawpathname

                # set start/end on the clips if they are set in the db
                # else None

                cut['in']=hms_to_clock(cl.start)
                cut['out']=hms_to_clock(cl.end)

                cut['length'] = cl.duration()
                # cut['length'] = cl.duration()

                if cl.episode.channelcopy:
                    cut['channelcopy'] = cl.episode.channelcopy
                else:
                    cut['channelcopy']='01'

                if cl.episode.normalise:
                    cut['normalize'] = cl.episode.normalise
                else:
                    cut['normalize']='-12.0'

                cuts.append(cut)

            return cuts

        params = {}
        params['title_img'] = get_title(episode)
        params['foot_img'] = get_foot(episode)
        params['clips'] = get_clips(rfs)
        params['cuts'] = get_cuts(cls)

        return params


        # then the trailer gets added to the xml
        # and a final version gets written out.  whacky.
        mlt_pathname = os.path.join(self.work_dir, "%s.mlt" % episode.slug)

    # parse the xml into a tree of nodes
            # mlt_template_name = os.path.join(self.show_dir,"bling/chiweb/chiweb.mlt")
        mlt_template_name = os.path.join(self.show_dir,
                                         os.path.split(
                                             os.path.abspath(__file__))[0],
                                         "bling",
                                         "chiweb/chiweb.mlt")
        # print mlt_template_name
        # mlt = open(mlt_template_name).read()
        # print mlt

        tree = xml.etree.ElementTree.XMLID(mlt)

# set the title to the title slide we just made
        # import code; code.interact(local=locals())

        title = tree[1]['title']
        title.attrib['resource'] = title_img

# get the dvfile placeholder and remove it from the tree
        dvfile = tree[1]['producer0']
        tree[0].remove(dvfile)

# add in the dv files
        pos = 1
        for rf in rfs:
            if self.options.load_temp:
                src_pathname = os.path.join(self.episode_dir, rf.filename)
                dst_path = os.path.join(
                    self.tmp_dir, episode.slug, os.path.dirname(rf.filename))
                rawpathname = os.path.join(
                    self.tmp_dir, episode.slug, rf.filename)
              # self.tmp_dir,episode.slug,rf.filename.replace(':','_'))
                cmds = [['mkdir', '-p', dst_path],
                        ['rsync', '--progress', '--size-only',
                            src_pathname, rawpathname]]
                self.run_cmds(episode, cmds)
            else:
                if rf.filename.startswith('\\'):
                    rawpathname = rf.filename
                else:
                    rawpathname = os.path.join(
                        self.episode_dir, rf.filename)

            # check for missing input file
            # typically due to incorrect fs mount
            if not os.path.exists(rawpathname):
                print "can't find rawpathname", rawpathname
                return False

            dvfile.attrib['id'] = "producer%s" % rf.id
            dvfile.attrib['resource'] = rawpathname
            new = xml.etree.ElementTree.Element('producer', dvfile.attrib)
            tree[0].insert(pos, new)
            pos += 1

# get the dv clip placeholder, remove it from the playlist
        clip = tree[1]['clip']
        playlist = tree[1]['playlist1']
        playlist.remove(clip)

# add in the clips
        pos = 1
        for cl in cls:
            print cl
            if cl.raw_file.duration:
                print "duration:", cl.raw_file.duration
                clip.attrib['id'] = "clip%s" % cl.id
                clip.attrib['producer'] = "producer%s" % cl.raw_file.id

                # set start/end on the clips if they are set in the db
                # else remove them,
                # ignoroe the error if they are not there to remove

                if cl.start:
                    in_frame = time2f(cl.start, self.fps)
                    clip.attrib['in'] = str(in_frame)
                else:
                    try:
                        del(clip.attrib['in'])
                    except KeyError:
                        pass

                if self.options.test:
                    out_frame = "300"
                    clip.attrib['out'] = str(out_frame)
                elif cl.end:
                    out_frame = time2f(cl.end, self.fps)
                    clip.attrib['out'] = str(out_frame)
                else:
                    try:
                        del(clip.attrib['out'])
                    except KeyError:
                        pass

                # add the new clip to the tree
                print clip.attrib
                new = xml.etree.ElementTree.Element('entry', clip.attrib)
                playlist.insert(pos, new)
                pos += 1

        # write out the xml we have so far
        # then pass it to melt to calc total frames

        mlt_xml = xml.etree.ElementTree.tostring(tree[0])
        open(mlt_pathname, 'w').write(mlt_xml)
        p = subprocess.Popen(
            ['melt', mlt_pathname, '-consumer', 'xml'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()

        # hack to remove "Plugin 1046 exists in both ...."
        # out = '\n'.join(
        #        l for l in out.split('\n') if not l.startswith('Plugin') )

        print out
        print "err", err

        t = xml.etree.ElementTree.XMLID(out)
        frames = t[1]['tractor1'].get('out')
        frames = int(frames)

        # fade in/out the audio of the main track
        # in is already set: 0-30 frames.
        # out needs to be set to last 30 frames
        fadeout = tree[1]['fadeout']
        # fadeout.set("in",str(frames-30))
        # fadeout.set("out",str(frames))
        fadeout.set("in", "-120")
        fadeout.set("out", "-90")

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
        if self.options.upload_formats == 'flac':
            normalise = ''
        if normalise and normalise != '0':
            if self.options.verbose:
                print "normalise:", normalise
            new = xml.etree.ElementTree.Element('filter',
                                                {'mlt_service': 'volume',
                                                 'normalise': normalise})
            playlist.insert(pos, new)

        # default defined here:
        # 01 is copy Left to Right
        channelcopy = episode.channelcopy or \
            episode.location.channelcopy or \
            "01"

        if channelcopy:
            if self.options.verbose:
                print 'channelcopy:', channelcopy
            # channelcopy should be 01 or 10.
            # or m/'mono' to kick in this hack
            if channelcopy == 'm':
                new = xml.etree.ElementTree.Element('filter',
                                                    {'mlt_service': 'mono', 'channels': '2'})
            else:
                fro, to = list(channelcopy)
                new = xml.etree.ElementTree.Element('filter',
                                                    {'mlt_service': 'channelcopy',
                                                     'from': fro, 'to': to})
            playlist.insert(pos, new)

        if self.options.upload_formats == 'flac':
            # mix channels to mono
            new = xml.etree.ElementTree.Element('filter',
                                                {'mlt_service': 'mono', 'channels': '2'})
            # this should be 1, but
            # "service=mono channels=1" lowers pitch
            # https://sourceforge.net/tracker/?func=detail&aid=2972735
            playlist.insert(pos, new)

            # super hack: remove a bunch of stuff that messes up flac
            # like the title and transistion from title to cut
            tree[0].remove(title)
            x = tree[1]['playlist0']
            # print x
            tree[0].remove(x)
            x = tree[1]['tractor0']
            tree[0].remove(x)

        if self.options.verbose:
            xml.etree.ElementTree.dump(tree[0])

        mlt_xml = xml.etree.ElementTree.tostring(tree[0])
        open(mlt_pathname, 'w').write(mlt_xml)

        if self.options.debug_log:
            mlt_xml = mlt_xml.replace('<', '&lt;').replace('>', '&gt;')
            mlt_xml = mlt_xml.replace('&', '&amp;')
            episode.description += "\n%s\n" % (mlt_xml,)
            episode.save()

        return mlt_pathname

    def enc_all(self, mlt_pathname, episode):

        def enc_one(ext):
            out_pathname = os.path.join(
                self.show_dir, ext, "%s.%s" % (episode.slug, ext))

            if ext == 'webm':

                parms = {
                    'dv_format': self.options.dv_format,
                    'mlt': mlt_pathname,
                    'out': out_pathname,
                    'threads': self.options.threads,
                    'test': '',
                }

               # cmds=["melt %s -profile dv_ntsc -consumer avformat:%s progress=1 acodec=libvorbis ab=128k ar=44100 vcodec=libvpx minrate=0 b=600k aspect=@4/3 maxrate=1800k g=120 qmax=42 qmin=10"% (mlt_pathname,out_pathname,)]
                cmds = [
                    "melt -profile %(dv_format)s %(mlt)s force_aspect_ratio=@64/45 -consumer avformat:%(out)s progress=1 threads=0 ab=256k vb=2000k quality=good deadline=good deinterlace=1 deinterlace_method=yadif" % parms]

            if ext == 'flv':
                cmds = [
                    "melt %(mlt)s -progress -profile %(dv_format)s -consumer avformat:%(out)s progressive=1 acodec=libfaac ab=96k ar=44100 vcodec=libx264 b=110k vpre=/usr/share/ffmpeg/libx264-hq.ffpreset" % parms]

            if ext == 'flac':
                # 16kHz/mono
                cmds = ["melt -verbose -progress %s -consumer avformat:%s ar=16000" %
                        (mlt_pathname, out_pathname)]

            if ext == 'mp3':
                cmds = ["melt -verbose -progress %s -consumer avformat:%s" %
                        (mlt_pathname, out_pathname)]

            if ext == 'mp4':
                # High Quality Master 720x480 NTSC

                parms = {
                    'dv_format': self.options.dv_format,
                    'mlt': mlt_pathname,
                    'out': out_pathname,
                    'threads': self.options.threads,
                    'test': '',
                }

                cmd = "melt -verbose -progress "\
                    "-profile %(dv_format)s %(mlt)s "\
                    "-consumer avformat:%(out)s "\
                    "threads=%(threads)s "\
                    "progressive=1 "\
                    "strict=-2 "\
                    "properties=x264-medium "\
                    "ab=256k "\
                    % parms

                cmd = cmd.split()
                # 2 pass causes no video track, so dumping this.
                # need to figure out how to switch between good and fast
                if False:
                    cmds = [cmd + ['pass=1'],
                            cmd + ['pass=2']]
                    if True:  # even faster!
                        cmds[0].append('fastfirstpass=1')
                else:
                    cmds = [cmd]

                # cmds.append( ["qt-faststart", tmp_pathname, out_pathname] )
                if self.options.rm_temp:
                    cmds.append(["rm", tmp_pathname])

            if ext == 'm4v':
                # iPhone
                tmp_pathname = os.path.join(
                    self.tmp_dir, "%s.%s" % (episode.slug, ext))
                # combine settings from 2 files
                ffpreset = open(
                    '/usr/share/ffmpeg/libx264-default.ffpreset').read().split('\n')
                ffpreset.extend(
                    open('/usr/share/ffmpeg/libx264-ipod640.ffpreset').read().split('\n'))
                ffpreset = [i for i in ffpreset if i]
                cmd = "melt %(mlt)s -progress -profile %(dv_format)s -consumer avformat:%(tmp)s s=432x320 aspect=@4/3 progressive=1 acodec=libfaac ar=44100 ab=128k vcodec=libx264 b=70k" % parms
                cmd = cmd.split()
                cmd.extend(ffpreset)
                cmds = [cmd]
                cmds.append(["qt-faststart", tmp_pathname, out_pathname])
                if self.options.rm_temp:
                    cmds.append(["rm", tmp_pathname])

            if ext == 'dv':
                out_pathname = os.path.join(
                    self.tmp_dir, "%s.%s" % (episode.slug, ext))
                cmds = ["melt -verbose -progress %s -consumer avformat:%s pix_fmt=yuv411p progressive=1" %
                        (mlt_pathname, out_pathname)]
            if ext == 'ogv':
                # melt/ffmpeg ogv encoder is loopy,
                # so make a .dv and pass it to ffmpeg2theora
                ret = enc_one("dv")
                if ret:
                    dv_pathname = os.path.join(
                        self.tmp_dir, "%s.dv" % (episode.slug,))
                    cmds = [
                        "ffmpeg2theora --videoquality 5 -V 600 --audioquality 5 --channels 1 %s -o %s" % (dv_pathname, out_pathname)]
                    if self.options.rm_temp:
                        cmds.append(["rm", dv_pathname])
                else:
                    return ret

            # run encoder:
            ret = self.run_cmds(episode, cmds)

            if ret and not os.path.exists(out_pathname):
                print "melt returned %ret, but no output: %s" % \
                    (ret, out_pathname)
                ret = False

            return ret

        ret = True
        # create all the formats for uploading
        for ext in self.options.upload_formats:
            print "encoding to %s" % (ext,)
            ret = enc_one(ext) and ret

        if self.options.enc_script:
            cmd = [self.options.enc_script,
                   self.show_dir, episode.slug]
            ret = ret and self.run_cmds(episode, [cmd])

        return ret

    def dv2theora(self, episode, dv_path_name, cls, rfs):
        """
        transcode dv to ogv
            """
        oggpathname = os.path.join(
            self.show_dir, "ogv", "%s.ogv" % episode.slug)
        # cmd="ffmpeg2theora --videoquality 5 -V 600 --audioquality 5 --speedlevel 0 --optimize --keyint 256 --channels 1".split()
        cmd = "ffmpeg2theora --videoquality 5 -V 600 --audioquality 5 --keyint 256 --channels 1".split()
        cmd += ['--output', oggpathname]
        cmd += [dv_path_name]
        return cmd

    def process_ep(self, episode):
        # print episode
        print episode.name

        ret = False

        cls = Cut_List.objects.filter(
            episode=episode, apply=True).order_by('sequence')
        # print len(cls), episode.name.__repr__()

        if cls:

            """
            for cl in cls:
                print cl.start, cl.end
            # title and footer were here
            title_img = self.mk_title(episode)

            credits_img = episode.show.client.credits \
                if episode.show.client.credits \
                else 'ndv1-black.png'
            credits_img = os.path.join(
                os.path.split(os.path.abspath(__file__))[0],
                "bling",
                credits_img)
            """

            # get list of raw footage for this episode
            rfs = Raw_File.objects. \
                filter(cut_list__episode=episode).\
                exclude(trash=True).distinct()
               #         cut_list__apply=True).\

            # get a .mlt file for this episode (mlt_pathname)
            # look for custom/slug.mlt and just use it, 
            # else build one from client.template_mlt, else "template.mlt"
            
            mlt_pathname = os.path.join(self.work_dir, "custom", "%s.mlt" % episode.slug)
            if os.path.exists(mlt_pathname):
                ret = True
            else:

                mlt_pathname = os.path.join(self.work_dir, "%s.mlt" % episode.slug)
                if episode.show.client.template_mlt:
                    template_mlt = episode.show.client.template_mlt
                else:
                    template_mlt = "template.mlt"
                
                params = self.get_params(episode, rfs, cls )
                ret = mk_mlt( template_mlt, mlt_pathname, params )

            if not ret:

                episode.state = 0
                episode.comment += "\nenc.py  mlt = self.mkmlt_1 failed.\n"
                episode.save()
                return False

# do the final encoding:
# using melt
            ret = self.enc_all(mlt_pathname, episode)

            if self.options.load_temp and self.options.rm_temp:
                cmds = []
                for rf in rfs:
                    dst_path = os.path.join(
                        self.tmp_dir, episode.slug, os.path.dirname(rf.filename))
                    rawpathname = os.path.join(
                        self.tmp_dir, episode.slug, rf.filename)
                    cmds.append(['rm', rawpathname])
                cmds.append(['rmdir', dst_path])
                dst_path = os.path.join(self.tmp_dir, episode.slug)
                cmds.append(['rmdir', dst_path])
                self.run_cmds(episode, cmds)

        else:

            err_msg = "No cutlist found."
            episode.state = 0
            episode.comment += "\nenc error: %s\n" % (err_msg,)
            episode.save()

            print err_msg
            return False

        if self.options.test:
            ret = False

        # save the episode so the test suite can get the slug
        self.episode = episode

        return ret

    def add_more_options(self, parser):
        parser.add_option('--enc-script',
                          help='encode shell script')
        parser.add_option('--load-temp', action="store_true",
                          help='copy .dv to temp files')
        parser.add_option('--rm-temp',
                          help='remove large temp files')
        parser.add_option('--threads')

    def add_more_option_defaults(self, parser):
        parser.set_defaults(threads=2)

if __name__ == '__main__':
    p = enc()
    p.main()
