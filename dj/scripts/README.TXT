# Veyepar 

Getting started...

1. install django, create the database
veyepar/dj$ ./manage.py syncdb

2. create a client and show records in the db
currently hardcoded into addeps.py: 

client,created = Client.objects.get_or_create(name='PyOhio',slug="pyohio")
show,created = Show.objects.get_or_create(name='PyOhio09',slug="pyohio09",client=client)

3. add episodes (what results in one video - a talk, a sigle event...)
addeps.py:# adds episodes from an external source, like a csv

Make sure the start/end times are right. the next step uses them.  you can fix the db later, but it is much easier if you get it right here, and the camera's clock was set.

4. create the dirs for the .dv files:
(I think there are hardcoded dates... fix that.)
mkdirs.py:# Makes the dir tree for dvsink-file to put files into
mkdirs.py:# os.makedirs("%s/%s/dv" % (root,show.slug))
mkdirs.py:    # dir="%s/%s/dv/%s" % (root,show.slug,dt)
mkdirs.py:         # dir="%s/%s/dv/%s/%s" % (root,show.slug,dt,loc.slug)

5. put the dv files into the dirs
rsync, mv, whatever.  

6. for all dv files, add records into the db:
adddv.py:# Adds the .dv files to the raw files table
adddv.py:                # find Episodes this may be a part of, add a cutlist record

This currently uses dvgrab to get the datetime from the file.  it has issues.
dvdate.py:# dvdate.py - gets date of .dv file - shells out to dvgrab

It also uses ocr to find some text, which makes for a good thumnail.
ocrdv.py:# ocrdv - reads frames from a .dv untill it finds a bunch of words
ocrdv.py:        # ocr the image
ocrdv.py:            # score the text
ocrdv.py:        frameno+=30*60  # bump on min

If you find that the clock was screwed up, you can adjust the datetime in the db:

fixdv.py:# tweaks the time in the other direction
fixdv.py:timetweak = -3600  # seconds to adjust file timestamp to reality (like timezones)


7. make low quality versions of all the dv files so you can preview each file in a browser using <video> (not necessary, didn't work too well, I used mplayer.)
dvogg.py:# makes .ogg for all dv in a show

8. for each episode, look at what .dv files have been assigned to it.  

http://0.0.0.0:8080/main/E/1 

If there are ones missing, either use fixdv.py to fix batches, or use django's admin UI to add one by one.  If a dv file has no useful content, mark it as Trash.  
If it belongs to some other event, mark "Cut List - Delete [x]"  This deletes the cutlist entry in the db, not the file.  Nothing deletes the file.

If a dv needs junk trimmed from the start or end, put the time offset in "Cut List - Start/End" 
1 or 0:0:1 means trim 1 second from start.  1:2:3 means the clip ends 1 hour 2 min 3 seconds from the start of the file, so in this case 1h 2m 2 seconds would be used.

Set Episode.state to 2 - not sure how this hapens :)

9. encode dv to ogg.  for Episodes with only 1 .dv file, that file will be the source.  
For more than one, the frames to be included will be copied into a .dv file, and that gets transcoded.  so have appropite amount of space.

enc.py:# encodes to ogg

10. post em:
post.py:# posts to blip.tv, tweets it
post.py:    # username,pwd = "blipuser","1234"

tweeter.py:     
# TWITTER_USERNAME, TWITTER_PASSWORD = ('twiteruser', '1234')
# BITLY_USERNAME, BITLY_API_KEY = ('bituser','R_d2f2c394eabcxyz37bd8b340eeb1234')

