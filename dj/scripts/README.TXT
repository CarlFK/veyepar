# Veyepar 

Getting started...

1. install django, create the database
veyepar/dj$ ./manage.py syncdb

2. create a client, show, location and episodes records in the db
Use the django admin UI for client and Show.  
If you have many Episodes it might be worth the effort to import locaion and episodes from a .csv file using addeps.py.  
Otherwise use the admin UI for location and episode too.

3. Make sure the start/end times are right. the next step uses them.  you can fix the db later, but it is much easier if you get it right here, and the camera's clock was set.  
If you don't know when someting started or ended, leave it blank.  This will link all .dv files to the episode.  It is easier to remvoe links than add them.

4. create the dirs for the .dv files:
mkdirs.py:# Makes the dir tree to put files into

4.1. put the dv files into the dirs
Use your mad file copy skilz to rsync, mv, whatever.  

5. for all dv files, add records into the db:
adddv.py:# Adds the .dv files to the raw files table
adddv.py:                # find Episodes this may be a part of, add a cutlist record
adddv.py: files=os.listdir(dir)
adddv.py: Raw_File.objects.get_or_create( filename=dv,)

6.0 collect dv metadata  
6.1 start/end
This currently uses dvgrab to get the datetime from the file.  it has issues.
dvdate.py:# dvdate.py - gets date of .dv file - shells out to dvgrab

6.2 ocr/thumbnail
use ocr to find some text, which makes for a good thumnail.
ocrdv.py:# ocrdv - reads frames from a .dv untill it finds a bunch of words
ocrdv.py:        # ocr the image
ocrdv.py:            # score the text
ocrdv.py:        frameno+=30*60  # bump on min

If you find that the clock was screwed up, you can adjust the datetime in the db:

fixdv.py:# tweaks the time in the other direction
fixdv.py:timetweak = -3600  # seconds to adjust file timestamp to reality (like timezones)


7. Associte dv files with Episodes.
assocdv.py: # creates cutlist items for dv files that might belong to an episode
        eps = Episode.objects.filter(
            Q(start__lte=dv.end)|Q(start__isnull=True),
            Q(end__gte=dv.start)|Q(end__isnull=True),
            location=dv.location).exclude(slug='orphans' )

8. make low quality versions of all the dv files so you can preview each file in a browser using <video> (not necessary, didn't work too well, I used mplayer.)
dvogg.py:# makes .ogg for all dv in a show

9. for each episode, look at what .dv files have been assigned to it.  

http://0.0.0.0:8080/main/E/1 

If there are ones missing, either use fixdv.py to fix batches, or use django's admin UI to add one by one.  If a dv file has no useful content, mark it as Trash.  
If it belongs to some other event, mark "Cut List - Delete [x]"  This deletes the cutlist entry in the db, not the file.  Nothing deletes the file.

If a dv needs junk trimmed from the start or end, put the time offset in "Cut List - Start/End" 
1 or 0:0:1 means trim 1 second from start.  1:2:3 means the clip ends 1 hour 2 min 3 seconds from the start of the file, so in this case 1h 2m 2 seconds would be used.

Set Episode.state to 2 - not sure how this hapens :)

10. encode dv to ogg.  for Episodes with only 1 .dv file, that file will be the source.  
For more than one, the frames to be included will be copied into a .dv file, and that gets transcoded.  so have appropite amount of space.

enc.py:# encodes to ogg

11. post em:
post.py:# posts to blip.tv, tweets it
pw.py holds user/passwords

