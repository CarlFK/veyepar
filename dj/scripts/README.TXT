# Veyepar 

Getting started...

1. install dependancies: INSTALL.sh
This installs all of the python modules in a virtualenv sandbox using virtualenvwrapper.  So before running any python apps, you must activate the virtualenv with:
workon veyepar.
This has been added to ~/.bashrc so it should be setup.
Then you must run everything with 
python <script name>.py
Running ./<script>.py won't work.
Using virtualenv makes develoment easier and reduces the amount of things that require root/sudo privs.  

1.1 create the database
veyepar/dj$ python ./manage.py syncdb
INSTAL.sh calls rt.sh (run tests) which will create the db and a test admin user.  For production you should start with a fresh db, so delete veyepar.db and ru  the above command.

2. create a location, client, show, and episode records in the db
http://localhost:8080 log in.
a. click "Locations"
b. enter Location Name, hit save. 
 tip: use hostname of box dvswitch is run on.
c. click "Clients"
d. enter Client Name, hit save.
f. enter Show Name, select Location from step b, hit Save.
g. click on show link
h. enter episode Name, start/duration - hit Save.
i. repeat for each Episode

3. veyepar.cfg: set client and show to the client and show slugs.  review settings,  pal/ntsc is one of the more important ones.

If you have many Episodes it might be worth the effort to import locaion and episodes from a json or .csv file using addeps.py.  

4. create the dirs for the .dv files:
mkdirs.py  # Makes the dir tree to put files into

4.1. copy the bling into the show's bling dir.
cp veyepar/dj/scripts/* ~/Videos/veyepar/test_client/test_show/bling/

4.2. put the dv files into the dirs
Use your mad file copy skilz to rsync, mv, whatever.  

5. for all dv files, add records into the db:
adddv.py:# Adds the .dv files to the raw files table
adddv.py:                # find Episodes this may be a part of, add a cutlist record
adddv.py: files=os.listdir(dir)
adddv.py: Raw_File.objects.get_or_create( filename=dv,)

6.0 collect dv metadata  
6.1 start/end
tsdv.py - timestamp dv
Gets start from one of:
the file name (assumes hh:mm:ss.dv format)
There is code to read the time stamp from the .dv file frames, but that doesn't work well at all.  

6.2 ocr/thumbnail
use ocr to find some text, which makes for a good thumnail.
mkthumbs.py - find thumbs, ocr untill we find some text

7. Associte dv files with Episodes.
create cutlist records for each intersection of a dv file and episodes start/end time and location.
assocdv.py: # creates cutlist items for dv files that might belong to an episode
        eps = Episode.objects.filter(
            Q(start__lte=dv.end)|Q(start__isnull=True),
            Q(end__gte=dv.start)|Q(end__isnull=True),
            location=dv.location).exclude(slug='orphans' )

8. make low quality versions of all the dv files so you can preview each file in a browser using <video> (not necessary, didn't work too well, I used mplayer.)
dvogg.py:# makes .ogg for all dv in a show

9. for each episode, look at what .dv files have been assigned to it.  

http://0.0.0.0:8080/main/E/1 

If there are ones missing, either use fixdv.py to fix batches, or use django's admin UI to add one by one.  

If it belongs to some other event, mark "Cut List - Delete [x]"  This deletes the cutlist entry in the db, not the file.  Nothing deletes the file.

If a dv needs junk trimmed from the start or end, put the time offset in "Cut List - Start/End" 
1 or 0:0:1 means trim 1 second from start.  1:2:3 means the clip ends 1 hour 2 min 3 seconds from the start of the file, so in this case 1h 2m 3 seconds would be used.

Set Episode.state to Encode (2)

10. encode files to upload
enc.py:# encodes to ogg, flv, m4v
adds titles too.

11. post em:
post.py:# posts to blip.tv, 
pw.py holds user/passwords, not checked in, make one from pw_samp.py

12. tweet 
tweet.py
