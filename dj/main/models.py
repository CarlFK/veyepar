# models.py

from django.db import models

class Client(models.Model):
    sequence = models.IntegerField(default=1)
    name = models.CharField(max_length=135)
    slug = models.CharField(max_length=135,help_text="dir name to store input files")
    def __unicode__(self):
        return self.name

class Show(models.Model):
    client = models.ForeignKey(Client)
    sequence = models.IntegerField(default=1)
    name = models.CharField(max_length=135)
    slug = models.CharField(max_length=135,help_text="dir name to store input files")
    @property
    def client_name(self):
        return self.client
    def __unicode__(self):
        return "%s: %s" % ( self.client_name, self.name )

class Location(models.Model):
    sequence = models.IntegerField(default=1)
    show = models.ForeignKey(Show)
    name = models.CharField(max_length=135,help_text="room name")
    slug = models.CharField(max_length=135,help_text="dir name to store input files")
    @property
    def show_name(self):
        return self.show
    def __unicode__(self):
        return "%s: %s" % ( self.show_name, self.name )

class Raw_File(models.Model):
    location = models.ForeignKey(Location)
    filename = models.CharField(max_length=135,help_text="pathname.dv")
    start = models.DateTimeField(null=True, blank=True, 
        help_text='when recorded (should agree with file name and timestamp)')
    end = models.DateTimeField(null=True, blank=True)
    comment = models.TextField(blank=True)
    def __unicode__(self):
        return self.filename

class Quality(models.Model):
    level = models.IntegerField()
    name = models.CharField(max_length=35)
    description = models.TextField(blank=True)
    def __unicode__(self):
        return self.name

class Episode(models.Model):
    location = models.ForeignKey(Location, null=True)
    sequence = models.IntegerField(null=True,blank=True,
        help_text="process order")
    primary = models.CharField(max_length=135,blank=True,
        help_text="pointer to master version of event (name,desc,time,author,files,etc)")
    name = models.CharField(max_length=135, help_text="(synced from primary source)")
    description = models.TextField(blank=True, help_text="(synced from primary source)")
    slug = models.CharField(max_length=135,help_text="used for file name")
    start = models.DateTimeField(null=True, blank=True, 
        help_text="initially scheduled time from master, adjusted to match reality")
    end = models.DateTimeField(null=True, blank=True)
    video_quality = models.ForeignKey(Quality,null=True,blank=True,related_name='video_quality')
    audio_quality = models.ForeignKey(Quality,null=True,blank=True,related_name='audio_quality')
    comment = models.TextField(blank=True, help_text="production notes")
    @property
    def location_name(self):
        return self.location
    def __unicode__(self):
        return "%s: %s" % ( self.location_name, self.name )

class Cut_List(models.Model):
    raw_file = models.ForeignKey(Raw_File)
    episode = models.ForeignKey(Episode)
    sequence = models.IntegerField(default=1)
    start = models.CharField(max_length=11, blank=True, 
        help_text='offset from start in HH:MM:SS.SS')
    end = models.CharField(max_length=11, blank=True,
        help_text='offset from start in HH:MM:SS.SS')
    comment = models.TextField(blank=True)
    def __unicode__(self):
        return "%s - %s" % (self.start, self.end)

class State(models.Model):
    sequence = models.IntegerField(default=1)
    slug = models.CharField(max_length=30)
    description = models.CharField(max_length=135, blank=True)

class Log(models.Model):
    episode = models.ForeignKey(Episode)
    state = models.ForeignKey(State)
    ready = models.DateTimeField()
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    result = models.CharField(max_length=130)



