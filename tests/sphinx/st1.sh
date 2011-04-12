#!/bin/bash -x

# sphinx test 1
# start with known good audio: goforward.16k
# $ sphinx2-test 2>&1 |grep BESTPATH
# INFO: searchlat.c(939): BESTPATH: GO FORWARD TEN METERS  (goforward -97741561)

# transcode with sox to goforwad.wav
# melt - encode to test.mp4
# melt - encode to test.wav 
# sox - to test.16k
# play test.16k (verify using human ear)
# trainscribe test.16k
# look for expected text: "GO FORWARD TEN METERS"

echo test1>source.txt
sox -b 16 -r 16k -e signed -c 1 -t raw \
     /usr/share/sphinx2/model/lm/turtle/goforward.16k \
     goforward.wav

melt -verbose \
 -profile dv_ntsc \
 -audio-track \
 goforward.wav \
 -video-track \
 source.txt \
 out=90 \
 -consumer avformat:test.mp4

melt test.mp4 -consumer avformat:test.wav
sox test.wav -b 16 -r 16k -e signed -c 1 -t raw test.16k 
     
# play -b 16 -r 16k -e signed -c 1 -t raw test.16k

HMM=/usr/share/sphinx2/model/hmm/6k
TURT=/usr/share/sphinx2/model/lm/turtle
TASK=.
CTLFILE=turtle.ctl

echo "using goforward.16k:    BESTPATH: GO FORWARD TEN METERS  goforward -97741561"


sphinx2-continuous -verbose 9 -adcin TRUE -adcext 16k -ctlfn test.ctl -ctloffset 0 -ctlcount 100000000 -datadir ${TASK} -agcmax TRUE -langwt 6.5 -fwdflatlw 8.5 -rescorelw 9.5 -ugwt 0.5 -fillpen 1e-10 -silpen 0.005 -inspen 0.65 -top 1 -topsenfrm 3 -topsenthresh -70000 -beam 2e-06 -npbeam 2e-06 -lpbeam 2e-05 -lponlybeam 0.0005 -nwbeam 0.0005 -fwdflat FALSE -fwdflatbeam 1e-08 -fwdflatnwbeam 0.0003 -bestpath TRUE -kbdumpdir ${TASK} -lmfn ${TURT}/turtle.lm -dictfn ${TURT}/turtle.dic -ndictfn ${HMM}/noisedict -phnfn ${HMM}/phone -mapfn ${HMM}/map -hmmdir ${HMM} -hmmdirlist ${HMM} -8bsen TRUE -sendumpfn ${HMM}/sendump -cbdir ${HMM} 2>&1|grep BESTPATH


rm test.16k test.wav test.mp4 source.txt goforward.wav

