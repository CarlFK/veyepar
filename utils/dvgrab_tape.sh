# dvgrab_tape.sh
# runs dvgrab to read from a tape in a camera

# -autosplit - start a new file ech time pause was hit for more than 1 second
# -rewind Rewind the tape first
# -showstatus for fun really
# -size=0 don't start new files (default is 1gig files)
# -timestamp date and time of recording into file name.
# 

dvgrab -autosplit -rewind -showstatus -size=0 -timestamp tape-

# the file names will be like: "tape-2013.08.06_12-02-17.dv"
