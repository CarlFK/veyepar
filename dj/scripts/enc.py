#!/usr/bin/python

"""
assembles raw cuts into final, titles, tweaks audio, encodes to format for upload.
"""
import os
import sys
import subprocess
import xml.etree.ElementTree

from mk_mlt import mk_mlt

import pprint
from process import process

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

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
                print("looking for:", key)
            # tollerate template where tokens have been removed
            if key in tree[1]:

                if key == "license":
                    # CC license image
                    if self.options.verbose:
                        print("found in svg:", tree[1][key])
                        print("replacing with:", texts[key])
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
                        print("found in svg:", tree[1][key].text)
                        print("replacing with:", texts[key])  # .encode()
                    tree[1][key].text = texts[key]

        # cooked_svg = xml.etree.ElementTree.tostring(tree[0])
        # print "testing...", "license" in cooked_svg

        if 'presenternames' in tree[1]:
            # some people like to add spiffy text near the presenter name(s)
            if texts['authors']:
                # prefix = u"Featuring" if "," in texts['authors'] else "By"
                # tree[1]['presenternames'].text=u"%s %s" % (prefix,texts['authors'])
                tree[1]['presenternames'].text = texts['authors']
            else:
                # remove the text (there is a placholder to make editing sane)
                tree[1]['presenternames'].text = ""

        cooked_svg = xml.etree.ElementTree.tostring(tree[0]).decode('ascii')

        return cooked_svg

    def get_title_text(self, episode):
        # lets try putting (stuff) on a new line
        title = episode.name
        authors = episode.authors

        if episode.show.slug == 'write_docs_na_2016':
            title = title.upper()
            authors = authors.upper()

        if False and episode.show.slug != 'pygotham_2015' and  len(title) > 80: # crazy long titles need all the lines  
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
        elif "? " in title:   # ?(space) to not break on 'can you?' 
            pos = title.index("?") + 1
            title, title2 = title[:pos], title[pos:].strip()
        elif ". " in title:
            pos = title.index(". ") + 1
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
        # split authors over two objects
        # breaking on comma, not space.
        if ',' in authors:
            authors = authors.split(', ')
            author2 = ', '.join(authors[1:])
            authors = authors[0].strip()
        else:
            author2 = ''
        """
        author2 = ''

        date = episode.start.strftime("%B %-d, %Y")

        # DebConf style
        # date = episode.start.strftime("%Y-%m-%-d")

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
        cmd = ["inkscape", svg_name,
               "--export-png", png_name,
               # "--export-width", "720",
               ]
        ret = self.run_cmds(episode, [cmd])
        ret = os.path.exists(png_name)

        # if self.options.verbose: print cooked_svg
        if self.options.verbose:
            print(png_name)

        if not ret:
            print("svg:", svg_name)
            png_name = None

        return png_name

    def mk_title(self, episode):
        # make a title slide

        # if we find titles/custom/(slug).svg, use that
        # else make one from the tempalte
        custom_svg_name = os.path.join( "..",
            "custom", "titles", episode.slug + ".svg")
        if self.options.verbose: print("custom:", custom_svg_name)
        abs_path =  os.path.join( self.show_dir, "tmp", custom_svg_name )
        if os.path.exists(abs_path):
            # cooked_svg_name = custom_svg_name
            cooked_svg_name = abs_path
        else:
            svg_name = episode.show.client.title_svg
            print(svg_name)
            template = os.path.join(
                os.path.split(os.path.abspath(__file__))[0],
                "bling",
                svg_name)

            raw_svg = open(template).read()

            # happy_filename = episode.slug.encode('utf-8')
            happy_filename = episode.slug
            # happy_filename = ''.join([c for c in happy_filename if c.isalpha()])
            # title_base = os.path.join(self.show_dir, "titles", happy_filename)
            title_base = os.path.join("..", "titles", happy_filename)
            texts = self.get_title_text(episode)
            cooked_svg = self.mk_title_svg(raw_svg, texts)

            # save svg to a file
            # strip 'broken' chars because inkscape can't handle the truth
            # output_base=''.join([ c for c in output_base if c.isalpha()])
            # output_base=''.join([ c for c in output_base if ord(c)<128])
            # output_base=output_base.encode('utf-8','ignore')

            cooked_svg_name = os.path.join(
                self.show_dir, "titles", '{}.svg'.format(episode.slug))
            open(cooked_svg_name, 'w').write(cooked_svg)

        png_name = os.path.join( "..",
            "titles", '{}.png'.format(episode.slug))

        abs_path = os.path.join( self.show_dir, "tmp", png_name ) 

        title_img = self.svg2png(cooked_svg_name, abs_path, episode)

        if title_img is None:
            print("missing title png")
            return False

        return png_name

    def get_params(self, episode, rfs, cls):
        """
        assemble a dict of params to send to mk_mlt
        mlt template, title screen image, 
        filter parameters (currently just audio) 
        and cutlist+raw filenames
        """
        def get_title(episode):
            # if we find show_dir/custom/titles/(slug).svg, use that
            # else make one from the tempalte
            custom_png_name = os.path.join(
                self.show_dir, "custom", "titles", episode.slug + ".png")
            print("custom:", custom_png_name)
            if os.path.exists(custom_png_name):
                title_img = custom_png_name
            else:
                title_img = self.mk_title(episode)

            return title_img

        def get_foot(episode):
            credits_img = episode.show.client.credits
            credits_pathname = os.path.join("..", "assets", credits_img )
            return credits_pathname

        def get_clips(rfs, ep):

            """
            return list of possible input files
            this may get the files and store them localy.
            start/end segments are under get_cuts.
            ps.  this is not used for encoding,
            just shows in ShotCut for easy dragging onto the timeline.
            """

            clips = []
            for rf in rfs:

                clip = {'id': rf.id }

                # if rf.filename.startswith('\\'):
                #     rawpathname = rf.filename
                # else:
                raw_pathname = os.path.join( "../dv", 
                        rf.location.slug, rf.filename)
                    # self.episode_dir, rf.filename)

                # check for missing input file
                # typically due to incorrect fs mount
                abs_path =  os.path.join( 
                        self.show_dir, "tmp", raw_pathname)
                
                if not os.path.exists(abs_path):
                    print(( 'raw_pathname not found: "{}"'.format(
                        abs_path)))
                    return False

                clip['filename']=raw_pathname

                # trim start/end based on episode start/end
                if rf.start < ep.start < rf.end:
                    # if the ep start falls durring this clip, 
                    # trim it
                    d = ep.start - rf.start
                    clip['in']="00:00:{}".format(d.total_seconds())
                else:
                    clip['in']=None

                # if "mkv" in rf.filename:
                #    import code; code.interact(local=locals())

                if rf.start < ep.end < rf.end:
                    # if the ep end falls durring this clip, 
                    d = ep.end - rf.start
                    clip['out']="00:00:{}".format(d.total_seconds())
                else:
                    clip['out']=None

                pprint.pprint(clip)

                clips.append(clip)

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

                rawpathname = os.path.join( "../dv", 
                        cl.raw_file.location.slug, cl.raw_file.filename)
                    # self.episode_dir, cl.raw_file.filename)
                # print(rawpathname)
                cut['filename'] = rawpathname

                # set start/end on the clips if they are set in the db
                # else None

                cut['in']=hms_to_clock(cl.start)
                cut['out']=hms_to_clock(cl.end)

                cut['length'] = cl.duration()

                if cl.episode.channelcopy:
                    cut['channelcopy'] = cl.episode.channelcopy
                else:
                    cut['channelcopy']='01'

                if cl.comment.startswith('channelcopy'):
                   channelcopy = cl.comment.split('\n')[0].split('=')[1].strip()
                   cut['channelcopy']=channelcopy

                if cl.episode.normalise:
                    cut['normalize'] = cl.episode.normalise
                else:
                    cut['normalize']='-12.0'

                if cl.episode.comment.startswith('delay'):
                    delay = cl.episode.comment.split('\n')[0].split('=')[1].strip()
                    cut['video_delay']=delay
                else:
                    if cl.episode.show.slug == "pygotham_2016":
                        cut['video_delay']='1.0'
                    else:
                        cut['video_delay']='0.0'

                cuts.append(cut)

            return cuts

        params = {}
        params['title_img'] = get_title(episode)
        params['foot_img'] = get_foot(episode)
        params['clips'] = get_clips(rfs, episode)
        params['cuts'] = get_cuts(cls)

        return params

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
                    "properties=x264-high "\
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

            if self.options.noencode:
                print("sorce files generated, skipping encode.")
                if self.options.melt:
                    self.run_cmd(['melt', mlt_pathname])
                ret = False
            else:
                # run encoder:
                ret = self.run_cmds(episode, cmds, )

                file_size = os.stat( out_pathname ).st_size
                print( out_pathname, file_size )

            # check results
            if ret and not os.path.exists(out_pathname):
                print("melt returned %ret, but no output: %s" % \
                    (ret, out_pathname))
                ret = False


            return ret

        ret = True
        # create all the formats for uploading
        for ext in self.options.upload_formats:
            print("encoding to %s" % (ext,))
            ret = enc_one(ext) and ret

        """
        if self.options.enc_script:
            cmd = [self.options.enc_script,
                   self.show_dir, episode.slug]
            ret = ret and self.run_cmds(episode, [cmd])
        """

        return ret

    def dv2theora(self, episode, dv_path_name, cls, rfs):
        """
        Not used any more.
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

        ret = False

        cls = Cut_List.objects.filter(
            episode=episode, apply=True).order_by('sequence')

        if cls:

            # get list of raw footage for this episode
            rfs = Raw_File.objects. \
                filter(cut_list__episode=episode).\
                exclude(trash=True).distinct()

            # get a .mlt file for this episode (mlt_pathname)
            # look for custom/slug.mlt and just use it, 
            # else build one from client.template_mlt
            
            mlt_pathname = os.path.join(
                    self.show_dir, "custom", 
                    "{}.mlt".format(episode.slug))

            if os.path.exists(mlt_pathname):
                print(("found custom/slug.mlt:\n{}".format( mlt_pathname )))
                ret = True
            else:

                template_mlt = episode.show.client.template_mlt
                
                mlt_pathname = os.path.join(self.show_dir, 
                        "mlt", "%s.mlt" % episode.slug)

                params = self.get_params(episode, rfs, cls )

                pprint.pprint(params)
                print((2, mlt_pathname))
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

            print(err_msg)
            return False

        if self.options.test:
            ret = False

        # save the episode so the test suite can get the slug
        self.episode = episode

        return ret

    def add_more_options(self, parser):
        parser.add_option('--enc-script',
                          help='encode shell script')
        parser.add_option('--noencode', action="store_true",
                          help="don't encode, just make svg, png, mlt")
        parser.add_option('--melt', action="store_true",
                          help="call melt slug.melt (only w/noencode)")
        parser.add_option('--load-temp', action="store_true",
                          help='copy .dv to temp files')
        parser.add_option('--rm-temp',
                          help='remove large temp files')
        parser.add_option('--threads', 
                          help='thread parameter passed to encoder')

    def add_more_option_defaults(self, parser):
        parser.set_defaults(threads=0)

if __name__ == '__main__':
    p = enc()
    p.main()
