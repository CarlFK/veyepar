#!/usr/bin/python

# Makes a bunch of ansible host_vars/hostname.yml files

import  os,sys

from process import process

from main.models import Client, Show, Location, Episode

class mk_conf(process):

    def mk_mix(self, i, loc, kags):
        filename = "/tmp/r{}mix.yml".format(i)
        print(filename)
        with open(filename, 'w') as f:
            f.write("""
---
org: {client}
show: {show}
room_name: {slug}

static_ip: 10.42.0.{i}0

irc_room_channel: "#lca2018-{slug}"
irc_nick: lcaav_{slug}

alsa_device: hw:1,0
audio_delay: 0

video_disk: /dev/sdb

sources:
- Camera1
- Grabber

streaming:
  method: rtmp
  hq_config:
    video_bitrate: 2000 # kbps
    audio_bitrate: 128000 # bps
    keyframe_period: 60 # seconds
  rtmp:
    vaapi: true
    location: !vault |
              $ANSIBLE_VAULT;1.1;AES256
              garblygook


""".format(i=i, slug=loc.slug, **kags))

    def mk_grab(self, i, loc, kags):
        filename = "/tmp/r{}grab.yml".format(i)
        print(filename)
        with open(filename, 'w') as f:
            f.write("""
---
static_ip: 10.42.0.{i}1
voctomix:
  host: 10.42.0.{i}0
  port: 10001
""".format(i=i, slug=loc.slug))


    def one_loc(self, i, loc, kags):
        self.mk_mix(i, loc, kags)
        self.mk_grab(i, loc, kags)


    def work(self):
        """
        find client and show, create the dirs
        """
        client = Client.objects.get(slug=self.options.client)
        show = Show.objects.get(client=client,slug=self.options.show)

        for i,loc in enumerate( Location.objects.filter(
                show=show, active=True).order_by('sequence') ):
            kags = {
                    'client': client.slug,
                    'show': show.slug,
                    }
            ret = self.one_loc(i+1,loc, kags)

        return

    def add_more_options(self, parser):
        parser.add_option('--raw-slugs', action="store_true", )

if __name__=='__main__':
    p=mk_conf()
    p.main()

