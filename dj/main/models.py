# models.py

import os
import socket
import datetime
import random
import re

from django import forms
from django import urls
from django.db import models
from django.db.models.signals import pre_save

from .unique_slugify import unique_slugify
from .titlecase import titlecase
from functools import reduce

def time2s(time):
    """ given 's.s' or 'h:m:s.s' returns s.s """
    if time:
        sec = reduce(lambda x, i: x*60 + i,
            list(map(float, time.split(':'))))
    else:
        sec = 0.0

    return sec


class Client(models.Model):
    sequence = models.IntegerField(default=1)
    active = models.BooleanField(default=True,
            help_text="Turn off to hide from UI.")
    name = models.CharField(max_length=135)
    slug = models.CharField(max_length=135, blank=True, null=False,
            help_text="dir name to store input files", )
    contacts = models.CharField(max_length=300, blank=True,
        help_text='emails of people putting on the event.')

    description = models.TextField(blank=True)
    tags = models.TextField(null=True,blank=True,)
    tweet_prefix = models.CharField(max_length=30, blank=True, null=True)
    bucket_id = models.CharField(max_length=30, blank=True, null=True)
    category_key = models.CharField(max_length=30, blank=True, null=True,
            help_text = "Category for Richard")

    # video encoding assets
    template_mlt = models.CharField(max_length=60, null=True,
        default="template.mlt",
        help_text='template to make cutlist mlt from.')
    title_svg = models.CharField(max_length=60, null=True,
        default="title.svg",
        help_text='template for event/title/authors title slide.')
    preroll = models.CharField(max_length=335, blank=True,
        help_text="name of video to prepend (not implemented)")
    postroll = models.CharField(max_length=335, blank=True,
        help_text="name of video to postpend (not implemented)")
    credits = models.CharField(max_length=30, blank=True,
            default="ndv-169.png",
        help_text='added to end, store in assets dir')

    # remote accounts to post to
    host_user = models.CharField(max_length=30, blank=True, null=True,
            help_text = "depricated - do not use.")

    youtube_id = models.CharField(max_length=10, blank=True, null=True,
            help_text = "key to lookup user/pw/etc from pw store" )
    archive_id = models.CharField(max_length=10, blank=True, null=True)
    vimeo_id = models.CharField(max_length=10, blank=True, null=True)
    blip_id = models.CharField(max_length=10, blank=True, null=True)
    rax_id = models.CharField(max_length=10, blank=True, null=True)
    richard_id = models.CharField(max_length=10, blank=True, null=True)
    email_id = models.CharField(max_length=10, blank=True, null=True)
    tweet_id = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return urls.reverse('client', [self.slug,])

    class Meta:
        ordering = ["sequence"]

class Location(models.Model):
    sequence = models.IntegerField(default=1)
    active = models.BooleanField( default=True,
        help_text="Turn off to hide from UI.")
    default = models.BooleanField(default=True,
        help_text="Adds this loc to new Clients.")
    name = models.CharField(max_length=135,
        help_text="room name")
    slug = models.CharField(max_length=135, blank=True, null=False,
        help_text="dir name to store input files")
    dirname = models.CharField(max_length=135, blank=True,
        help_text="path to raw files. overrieds show/slug.")
    channelcopy = models.CharField(max_length=2, blank=True,
        help_text='audio adjustment for this room')
    hours_offset =  models.IntegerField(blank=True, null=True,
        help_text='Adjust for bad clock setting')
    description = models.TextField(blank=True)
    lat = models.FloatField(null=True, blank=True,
            help_text='90=North Pole')
    lon = models.FloatField(null=True, blank=True,
            help_text='US is negative')

    def natural_key(self):
        return self.name

    def __str__(self):
        return "%s" % ( self.name )

    class Meta:
        ordering = ["name"]

ANN_STATES=((1,'preview'),(2,'review'),(3,'approved'))
class Show(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    locations = models.ManyToManyField(Location,
            limit_choices_to={'active': True},
            blank=True)
    sequence = models.IntegerField(default=1)
    active = models.BooleanField( default=True,
            help_text="Turn off to hide from UI.")
    name = models.CharField(max_length=135)
    slug = models.CharField(max_length=135, blank=True, null=False,
        help_text="dir name to store input files")
    category_key = models.CharField(max_length=30, blank=True, null=True,
            help_text = "Category for Richard")
    youtube_playlist_id = models.CharField(max_length=50, blank=True, null=True,
            help_text = "Playlist ID for YouTube")
    tags = models.TextField(null=True,blank=True,)
    description = models.TextField(blank=True)
    conf_url = models.CharField(max_length=200, null=True, blank=True)
    schedule_url = models.CharField(max_length=235, null=True, blank=True)
    announcement_state = models.IntegerField(null=True, blank=True,
        choices=ANN_STATES, default=ANN_STATES[1][0], )
    @property
    def client_name(self):
        return self.client
    def __str__(self):
        return "%s: %s" % ( self.client_name, self.name )
    # @models.permalink
    def get_absolute_url(self):
        return ('episode_list', [self.client.slug,self.slug,])
    class Meta:
        ordering = ["sequence"]

class Raw_File(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    show = models.ForeignKey(Show, on_delete=models.CASCADE)
    filename = models.CharField(max_length=135,help_text="filename.dv")
    filesize = models.BigIntegerField(default=1,help_text="size in bytes")
    start = models.DateTimeField(null=True, blank=True,
        help_text='when recorded (should agree with file name and timestamp)')
    duration = models.CharField(max_length=11, blank=True, )
    end = models.DateTimeField(null=True, blank=True)
    trash = models.BooleanField(default=False,
            help_text="This clip is trash")
    ocrtext = models.TextField(null=True,blank=True)
    comment = models.TextField(blank=True)

    def __next__(self):
        """
        gets the next clip in the room.
        """
        rfs = Raw_File.objects.filter(location=self.location,
                start__gt=self.start,
                ).order_by('start','id')
                # id__gt=self.id).order_by('start','id')
        if rfs:
            rf=rfs[0]
        else:
            rf=None

        return rf

    def basename(self):
        # strip the extension
        # good for making 1-2-3/foo.png from 1-2-3/foo.dv
        raise "homey don't play that no more."
        return os.path.splitext(self.filename)[0]

    def base_url(self):
        """ Returns the url for the file, minus the MEDIA_URL and extension """
        return "%s/%s/dv/%s/%s" % (self.show.client.slug,
                                    self.show.slug,
                                    self.location.slug,
                                    self.filename)

    @property
    def get_adjusted_start(self):
        return self.start + datetime.timedelta(
            hours = 0 if self.location.hours_offset is None
                else self.location.hours_offset )

    @property
    def get_adjusted_end(self):
        return self.end + datetime.timedelta(
            hours = 0 if self.location.hours_offset is None
                else self.location.hours_offset )

    def get_start_seconds(self):
        return time2s( self.start )

    def get_end_seconds(self):
        return time2s( self.end )

    def get_seconds(self):
        # return durration in seconds (float)
        delta = self.end - self.start
        seconds = delta.days*24*60*60 + delta.seconds
        return seconds

    def get_minutes(self):
        # return durration in minutes (float)
        return self.get_seconds()/60.0

    def __str__(self):
        return self.filename

    def get_absolute_url(self):
        return urls.reverse('raw_file', kwargs={"raw_file_id": self.id})
        # return reverse("people-detail", kwargs={"pk": self.pk})
        # return ('raw_file', [self.id,])

    class Meta:
        ordering = ["start", "location", "filename"]

class Mark(models.Model):
    show = models.ForeignKey(Show, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    click = models.DateTimeField(
        help_text='When Cut was Clicked.')

    class Meta:
        ordering = ["click"]

    def __str__(self):
        return self.click.isoformat()

class Quality(models.Model):
    level = models.IntegerField()
    name = models.CharField(max_length=35)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name

STATES=[
 (0, 'borked'),
 (1, 'edit'), # enter cutlist data
 (2, 'encode'), # assemble raw assets into final cut
 (3, 'push to queue'), # push to data center box
 (4, 'post'), # push to yourube and archive.org
 (5, 'richard'), # push urls and description to PyVideo.org
 (6, 'review 1'), # staff check to see if they exist on yourube/archive
 (7, 'email'), # send private url to presenter, ask for feedback,
 (8, 'review 2'), # wait for presenter to say good, or timeout
 (9, 'make public'), # flip private to public
 (10, 'tweet'), # tell world
 (11, 'to-miror'),
 (12, 'conf'),
 (13, 'done')
 ]


def generate_edit_key():
    """ Generate a random key """
    return str(random.randint(10000000,99999999))


class Episode(models.Model):
    show = models.ForeignKey(Show, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, null=True, on_delete=models.CASCADE)
    active = models.BooleanField(default=True,
            help_text="Turn off to hide from UI.")
    state = models.IntegerField(null=True, blank=True,
        choices=STATES, default=STATES[1][0],
        help_text="" )
    locked = models.DateTimeField(null=True, blank=True,
        help_text="clear this to unlock")
    locked_by = models.CharField(max_length=35, blank=True,
	    help_text="user/process that locked." )
    sequence = models.IntegerField(null=True,blank=True,
        help_text="process order")
    start = models.DateTimeField(blank=True, null=False,
        help_text="initially scheduled time from master, adjusted to match reality")
    duration = models.CharField(max_length=15,null=True,blank=True,
        help_text="length in hh:mm:ss")
    end = models.DateTimeField(blank=True, null=False,
        help_text="(calculated if start and duration are set.)")
    name = models.CharField(max_length=170,
        help_text="Video Title (shows in video search results)")
    slug = models.CharField(max_length=135, blank=True, null=False,
        help_text="file name friendly version of name")
    priority = models.IntegerField(null=True,blank=True,
        help_text="lower may not get recorded")
    released = models.BooleanField(
        null=True,
        help_text="has someone authorised pubication")
    conf_key = models.CharField(max_length=32, blank=True,
        help_text='primary key of event in conference system database.')
    conf_url = models.CharField(max_length=335,blank=True,default='',
        help_text="Event's details on conference site  (name,desc,time,author,files,etc)")
    conf_meta = models.TextField(blank=True,default='', null=True,
        help_text="Data provided by API")

    authors = models.TextField(null=True,blank=True,)
    emails = models.TextField(null=True,blank=True,
        help_text="email(s) of the presenter(s)")
    twitter_id = models.CharField(max_length=135, blank=True, null=True,
        help_text="Data provided by API")
    reviewers = models.TextField(blank=True,
        help_text="email(s) of the reviewers(s)")

    language = models.CharField(max_length=20, blank=True, null=True,
        help_text="Spoken languge (German, English...)")

    edit_key = models.CharField(max_length=32,
        blank=True,
        null=True,
        default=generate_edit_key,
        help_text="key to allow unauthenticated users to edit this item.")

    summary = models.TextField(blank=True, help_text="short", null=True)
    description = models.TextField(blank=True, help_text="markdown")
    tags = models.CharField(max_length=175,null=True,blank=True,)

    normalise = models.CharField(max_length=5,null=True,blank=True, )
    channelcopy = models.CharField(max_length=2,null=True,blank=True,
          help_text='m=mono, 01=copy left to right, 10=right to left, 00=ignore.' )

    license = models.CharField(max_length=20, null=True,blank=True,
            default='CC BY-SA',
            help_text='see http://creativecommons.org/licenses/')
    hidden = models.BooleanField(
        null=True,
        help_text='hidden (does not show up on public episode list')

    thumbnail = models.CharField(max_length=135,blank=True,
        help_text="filename.png" )
    host_url = models.CharField(max_length=235, null=True,blank=True,
        help_text = "URL of page video is hosted")
    public_url = models.CharField(max_length=335, null=True,blank=True,
        help_text = "URL public should use (like pvo or some aggregator")
    archive_ogv_url = models.CharField(max_length=355, null=True,blank=True,
        help_text = "URL public can use to dl an ogv (like archive.org")
    archive_url = models.CharField(max_length=355, null=True,blank=True,
        help_text = "not sure.. deprecated?")
    archive_mp4_url = models.CharField(max_length=355, null=True,blank=True,
        help_text = "URL public can use to dl an mp4. (like archive.org")
    rax_mp4_url = models.CharField(max_length=355, null=True,blank=True,
        help_text = "URL public can use to get an mp4. (like rackspace cdn")
    twitter_url = models.CharField(max_length=135, null=True,blank=True,
        help_text = "URL of tweet to email presenters for retweeting")

    video_quality = models.ForeignKey(Quality,null=True,blank=True,related_name='video_quality', on_delete=models.CASCADE)
    audio_quality = models.ForeignKey(Quality,null=True,blank=True,related_name='audio_quality', on_delete=models.CASCADE)

    comment = models.TextField(blank=True, help_text="production notes")

    stop = models.BooleanField(
        null=True,
        default=False,
        help_text="Stop process.py from processing anymore")

    formfield_overrides = {
            models.TextField: {
                'widget': forms.Textarea({'cols': 30, 'rows': 2}),
            }}

    class Meta:
        ordering = ["sequence"]
        # unique_together = [("show", "slug")]

    # @models.permalink
    def get_absolute_url(self):
        return ('episode', [self.id])

    def __str__(self):
        return self.name

    def cuts_time(self):
        # get total time in seoonds of video based on selected cuts.
        # or None if there are no clips.
        cuts = Cut_List.objects.filter(episode=self, apply=True)
        if not cuts:
            ret = None
        else:
            s=0
            for cut in cuts:
                s+=int(cut.duration()) # durration is in seconds :p
            ret = s

        return ret

    def get_minutes(self):
        ct = self.cuts_time()
        if ct is None:
            # if there are no cuts, use scheduled time
            delta = self.end - self.start
            minutes = delta.days*60*24 + delta.seconds/60.0
        else:
            # use amount of video time
            minutes = self.cuts_time()/60

        return int(minutes)

    def add_email(self, email):
        if self.emails is None: emails=[]
        else: emails = self.emails.split(',')
        if email not in emails:
            if self.emails:
                emails.append(email)
                self.emails = ','.join(emails)
            else:
                self.emails = email
            self.save()

    def get_authors(self):
        authors = self.authors.split(',') if self.authors else []
        return authors

    @property
    def titlecase(self):
        return titlecase(self.name)

    @property
    def location_slug(self):
        location_slug=self.location.slug
        print(location_slug)
        return location_slug

    def approve_url(self):
        url = "https://veyepar.nextdayvideo.com/main/approve/{id}/{slug}/{edit_key}/".format(id=self.id, slug=self.slug, edit_key=self.edit_key)
        return url

    def composed_description(self):
        # build a wad of text to use as public facing description

        show = self.show
        client = show.client

        footer = "Produced by NDV: https://youtube.com/channel/UCQ7dFBzZGlBvtU2hCecsBBg?sub_confirmation=1"

        # (show tags seperate the talk from the event text)
        descriptions = [self.authors,
                self.public_url,
                self.conf_url,
                self.description,
                show.tags,
                show.description,
                client.description,
                client.tags,
                "{} at {}".format(
                    self.start.strftime("%c"),
                    self.location.name),
                footer,
                ]

        # remove blanks
        descriptions = [d for d in descriptions if d]
        # combine wiht CRs between each item
        description = "\n\n".join(descriptions)
        # remove extra blank lines
        description = re.sub( r'\n{2,}', r'\n\n', description)
        # description = "<br/>\n".join(description.split('\n'))

        return description


class Cut_List(models.Model):
    """
    note: this sould be Cut_list_ITEM
    because it is not the whole list, just one entry.
    """
    raw_file = models.ForeignKey(Raw_File, on_delete=models.CASCADE)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    sequence = models.IntegerField(default=1)
    start = models.CharField(max_length=11, blank=True,
        help_text='offset from start in HH:MM:SS.ss')
    end = models.CharField(max_length=11, blank=True,
        help_text='offset from start in HH:MM:SS.ss')
    apply = models.BooleanField(default=1)
    comment = models.TextField(blank=True)
    def get_absolute_url(self):
        return urls.reverse('episode', [self.episode.id])
    def __str__(self):
        return "%s - %s" % (self.raw_file, self.episode.name)
    class Meta:
        ordering = ["sequence"]

    def get_start_seconds(self):
        return time2s( self.start )

    def get_start_wall(self):
        if self.start:
            return self.raw_file.start + \
                    datetime.timedelta(seconds=self.get_start_seconds())
        else:
            return self.raw_file.start

    def get_end_seconds(self):
        return time2s( self.end )

    def get_end_wall(self):
        if self.end:
            return self.raw_file.start + \
                    datetime.timedelta(seconds=self.get_end_seconds())
        else:
            return self.raw_file.end



    def duration(self):
        # calc size of clip in secconds
        # may be size of raw, but take into account trimming start/end
        def to_sec(time, default=0):
            # convert h:m:s to s
            if time:
                sec = reduce(lambda x, i: x*60 + i,
                    list(map(float, time.split(':'))))
            else:
                sec=default
            return sec
        start = to_sec( self.start )
        end = to_sec( self.end, to_sec(self.raw_file.duration))
        dur = end-start
        return dur

    def duration_hms(self):
        seconds = self.duration()
        hms = seconds//3600, (seconds%3600)//60, seconds%60
        duration = "%02d:%02d:%02d" % hms
        return duration

    def base_url(self):
        """ Returns the url for the file, minus the MEDIA_URL and extension """
        return self.raw_file.base_url()

class State(models.Model):
    sequence = models.IntegerField(default=1)
    slug = models.CharField(max_length=30)
    description = models.CharField(max_length=135, blank=True)
    command = models.CharField(max_length=135, blank=True)
    class Meta:
        ordering = ["sequence"]
    def __str__(self):
        return self.slug

class Image_File(models.Model):
    show = models.ForeignKey(Show, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, null=True, on_delete=models.CASCADE)
    episodes = models.ManyToManyField(Episode, blank=True)
    filename = models.CharField(max_length=135, help_text="foo.png")
    text = models.TextField(blank=True, help_text="OCRed text")

    def get_absolute_url(self):
        #  https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlencode
        url = "{}?{}={}".format(
                urls.reverse( 'admin:main_episode_changelist'),
                "image_file__id__exact",
                self.id)
        return url


class Log(models.Model):
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    state = models.ForeignKey(State, null=True, blank=True, on_delete=models.CASCADE)
    ready = models.DateTimeField()
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    user = models.CharField(max_length=50)
    result = models.CharField(max_length=250)

    def duration(self):
        if self.start and self.end:
            dur = self.end - self.start
            dur = datetime.timedelta(dur.days,dur.seconds)
            return dur
        else:
            return None

    # @models.permalink
    def get_absolute_url(self):
        return ('episode', [self.episode.id])

def set_slug(sender, instance, **kwargs):
    if not instance.slug or instance.slug is None:
    #    instance.slug = fnify(instance.name)
        return unique_slugify(instance, instance.name)

def set_end(sender, instance, **kwargs):
    if instance.start:
        if instance.duration:
            seconds = reduce(lambda x, i: x*60 + i,
                list(map(float, instance.duration.split(':'))))
            instance.end = instance.start + \
               datetime.timedelta(seconds=seconds)
        elif instance.end:
            # calc duration based on End
            d = instance.end - instance.start
            seconds = d.total_seconds()
            hms = seconds//3600, (seconds%3600)//60, seconds%60
            instance.duration = "%02d:%02d:%02d" % hms
        else:
            instance.end = None
    else:
        instance.end = None


pre_save.connect(set_slug,sender=Location)
pre_save.connect(set_slug,sender=Episode)

pre_save.connect(set_end,sender=Episode)
pre_save.connect(set_end,sender=Raw_File)

