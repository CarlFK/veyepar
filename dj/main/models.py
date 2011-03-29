# models.py

from django.db import models
from django.db.models.signals import pre_save

import os
import socket
import datetime

def fnify(text):
    """
    file_name_ify - make a file name out of text, like a talk title.
    convert spaces to _, remove junk like # and quotes.
    like slugify, but more file name friendly.
    """
    fn = text.replace(' ','_')
    fn = ''.join([c for c in fn if c.isalpha() or c.isdigit() or (c in '_') ])
    return fn


class Client(models.Model):
    sequence = models.IntegerField(default=1)
    active = models.BooleanField(help_text="Turn off to hide from UI.")
    name = models.CharField(max_length=135)
    slug = models.CharField(max_length=135,help_text="dir name to store input files")
    tags = models.TextField(null=True,blank=True,)
    description = models.TextField(blank=True)
    preroll = models.CharField(max_length=135, blank=True, 
        help_text="name of video to prepend (not implemented)")
    postroll = models.CharField(max_length=135, blank=True,
        help_text="name of video to postpend (not implemented)")
    blip_user = models.CharField(max_length=30, blank=True, null=True)
    title_svg = models.CharField(max_length=30, blank=True, null=True,
        help_text='template for event/title/authors')
    credits = models.CharField(max_length=30, blank=True, 
        help_text='template for ending credits')
    def __unicode__(self):
        return self.name
    @models.permalink
    def get_absolute_url(self):
        return ('client', [self.slug,])
    class Meta:
        ordering = ["sequence"]

class Location(models.Model):
    sequence = models.IntegerField(default=1)
    hostname because dvs-mon defaults to saving data in the same dirname
    active = models.BooleanField(help_text="Turn off to hide from UI.")
    default = models.BooleanField(default=True,
        help_text="Adds this loc to new Clients.")
    name = models.CharField(max_length=135, 
        default=socket.gethostname(),
        help_text="room name")
    slug = models.CharField(max_length=135,
        help_text="dir name to store input files")
    description = models.TextField(blank=True)
    def __unicode__(self):
        return "%s" % ( self.name )
    class Meta:
        ordering = ["sequence"]

class Show(models.Model):
    client = models.ForeignKey(Client)
    locations = models.ManyToManyField(Location)
    sequence = models.IntegerField(default=1)
    name = models.CharField(max_length=135)
    slug = models.CharField(max_length=135,
        help_text="dir name to store input files")
    tags = models.TextField(null=True,blank=True,)
    description = models.TextField(blank=True)
    @property
    def client_name(self):
        return self.client
    def __unicode__(self):
        return "%s: %s" % ( self.client_name, self.name )
    @models.permalink
    def get_absolute_url(self):
        return ('episode_list', [self.client.slug,self.slug,])
    class Meta:
        ordering = ["sequence"]

class Raw_File(models.Model):
    location = models.ForeignKey(Location)
    show = models.ForeignKey(Show)
    filename = models.CharField(max_length=135,help_text="filename.dv")
    filesize = models.BigIntegerField(default=1,help_text="size in bytes")
    start = models.DateTimeField(null=True, blank=True,
        help_text='when recorded (should agree with file name and timestamp)')
    duration = models.CharField(max_length=11, blank=True, )
    end = models.DateTimeField(null=True, blank=True)
    trash = models.BooleanField(help_text="This clip is trash")
    ocrtext = models.TextField(null=True,blank=True)
    comment = models.TextField(blank=True)
    def basename(self):
        # strip the extension
        # good for making foo.png from foo.dv
        return os.path.splitext(self.filename)[0]
    def __unicode__(self):
        return self.filename

    class Meta:
        ordering = ["filename"]


class Quality(models.Model):
    level = models.IntegerField()
    name = models.CharField(max_length=35)
    description = models.TextField(blank=True)
    def __unicode__(self):
        return self.name

STATES=((0, 'borked'), (1,'edit'),(2,'encode'),(3,'review'),(4,'post',),(5,'tweet'),(6,'done'))
class Episode(models.Model):
    show = models.ForeignKey(Show)
    location = models.ForeignKey(Location, null=True)
    active = models.BooleanField(help_text="Turn off to hide from UI.")
    state = models.IntegerField(null=True, blank=True,
        choices=STATES, default=STATES[1][0],
        help_text="2=ready to encode, 4=ready to post, 5=tweet" )
    locked = models.DateTimeField(null=True, blank=True, 
        help_text="clear this to unlock")
    locked_by = models.CharField(max_length=35, blank=True,
	    help_text="user/process that locked." )
    sequence = models.IntegerField(null=True,blank=True,
        help_text="process order")
    start = models.DateTimeField(blank=True, null=True,
        help_text="initially scheduled time from master, adjusted to match reality")
    duration = models.CharField(max_length=15,null=True,blank=True,
        help_text="length in hh:mm:ss")
    end = models.DateTimeField(blank=True, null=True,
        help_text="(calculated if start and duration are set.)")
    name = models.CharField(max_length=135, 
        help_text="(synced from primary source)")
    slug = models.CharField(max_length=135,
        help_text="file name friendly version of name")
    released = models.NullBooleanField(null=True,blank=True,
        help_text="has someone authorised pubication")
    conf_key = models.CharField(max_length=32, blank=True,
        help_text='primary key of event in conference system database.')
    conf_url = models.CharField(max_length=135,blank=True,
        help_text="event's details on conference site  (name,desc,time,author,files,etc)")
    authors = models.TextField(null=True,blank=True,)
    description = models.TextField(blank=True, help_text="(synced from primary source)")
    tags = models.CharField(max_length=135,null=True,blank=True,)
    normalise = models.CharField(max_length=5,null=True,blank=True, )

    channelcopy = models.CharField(max_length=2,null=True,blank=True,
          help_text='m=mono, 10=copy left to right, 01=right to left.' )
    license = models.IntegerField(null=True,blank=True,default=13,
        help_text='see http://0.0.0.0:8080/main/C/test_client/S/test_show/')
    hidden = models.NullBooleanField(null=True,blank=True,
        help_text='hidden on blip (does not show up on public episode list')
    thumbnail = models.CharField(max_length=135,blank=True, 
        help_text="filename.png" )
    target = models.CharField(max_length=135, null=True,blank=True,
        help_text = "Blip.tv episode ID")
    video_quality = models.ForeignKey(Quality,null=True,blank=True,related_name='video_quality')
    audio_quality = models.ForeignKey(Quality,null=True,blank=True,related_name='audio_quality')
    comment = models.TextField(blank=True, help_text="production notes")
    stop = models.NullBooleanField(
             help_text="Stop process.py from processing anymore")
    @models.permalink
    def get_absolute_url(self):
        return ('episode', [self.id])

    # better version of django's get_next.. (this handles nuls).
    def _get_next_or_previous_by_FIELD(self, field, is_next, **kwargs):
        from django.utils.encoding import smart_str
        from django.db.models.query import Q
        op = is_next and 'gt' or 'lt'
        order = not is_next and '-' or ''
        # current_field_value = getattr(self, field.attname)
        current_field_value = self.start
        if current_field_value is None:
            # q = Q(**{ "%s__isnull" % field.name: True, 'pk__%s' % op: self.pk})
            q = Q(**{ "%s__isnull" % 'start': True, 'pk__%s' % op: self.pk})
        else:
            param = smart_str(current_field_value)
            # q = Q(**{'%s__%s' % (field.name, op): param})
            q = Q(**{'%s__%s' % ('start', op): param})
            # q = q|Q(**{field.name: param, 'pk__%s' % op: self.pk})
            q = q|Q(**{'start': param, 'pk__%s' % op: self.pk})
 
    def my_get_previous_by_start(self,**kwargs):
        self._get_next_or_previous_by_FIELD('start', is_next=False, **kwargs)
    def my_get_next_by_start(self,**kwargs):
        self._get_next_or_previous_by_FIELD('start', is_next=True, **kwargs)
 
           
    def __unicode__(self):
        return "%s: %s" % ( self.id, self.name )
        return "%s: %s" % ( self.location.name, self.name )
    class Meta:
        ordering = ["sequence"]

  

class Cut_List(models.Model):
    raw_file = models.ForeignKey(Raw_File)
    episode = models.ForeignKey(Episode)
    sequence = models.IntegerField(default=1)
    start = models.CharField(max_length=11, blank=True, 
        help_text='offset from start in HH:MM:SS.SS')
    end = models.CharField(max_length=11, blank=True,
        help_text='offset from start in HH:MM:SS.SS')
    apply = models.BooleanField(default=1)
    comment = models.TextField(blank=True)
    @models.permalink
    def get_absolute_url(self):
        return ('episode', [self.episode.id])
    def __unicode__(self):
        return "%s - %s" % (self.raw_file, self.episode)
    class Meta:
        ordering = ["sequence"]
    

class State(models.Model):
    sequence = models.IntegerField(default=1)
    slug = models.CharField(max_length=30)
    description = models.CharField(max_length=135, blank=True)
    class Meta:
        ordering = ["sequence"]

class Log(models.Model):
    episode = models.ForeignKey(Episode)
    state = models.ForeignKey(State, null=True, blank=True)
    ready = models.DateTimeField()
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    user = models.CharField(max_length=50)
    result = models.CharField(max_length=250)

def set_slug(sender, instance, **kwargs):
    if not instance.slug and instance.name:
        instance.slug = fnify(instance.name)

def set_end(sender, instance, **kwargs):
    if instance.start and instance.duration:
        seconds = reduce(lambda x, i: x*60 + i,
            map(float, instance.duration.split(':')))
        instance.end = instance.start + \
           datetime.timedelta(seconds=seconds)
    else:
        instance.end = None

pre_save.connect(set_slug,sender=Location)
pre_save.connect(set_slug,sender=Episode)

pre_save.connect(set_end,sender=Episode)
pre_save.connect(set_end,sender=Raw_File)

