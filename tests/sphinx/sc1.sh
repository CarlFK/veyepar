#!/bin/sh
HMM=/usr/share/sphinx2/model/hmm/6k
TURT=/usr/share/sphinx2/model/lm/turtle
TASK=.
CTLFILE=turtle.ctl

echo "using goforward.16k:    BESTPATH: GO FORWARD TEN METERS  goforward -97741561"


sphinx2-continuous -verbose 9 -adcin TRUE -adcext 16k -ctlfn test.ctl -ctloffset 0 -ctlcount 100000000 -datadir ${TASK} -agcmax TRUE -langwt 6.5 -fwdflatlw 8.5 -rescorelw 9.5 -ugwt 0.5 -fillpen 1e-10 -silpen 0.005 -inspen 0.65 -top 1 -topsenfrm 3 -topsenthresh -70000 -beam 2e-06 -npbeam 2e-06 -lpbeam 2e-05 -lponlybeam 0.0005 -nwbeam 0.0005 -fwdflat FALSE -fwdflatbeam 1e-08 -fwdflatnwbeam 0.0003 -bestpath TRUE -kbdumpdir ${TASK} -lmfn ${TURT}/turtle.lm -dictfn ${TURT}/turtle.dic -ndictfn ${HMM}/noisedict -phnfn ${HMM}/phone -mapfn ${HMM}/map -hmmdir ${HMM} -hmmdirlist ${HMM} -8bsen TRUE -sendumpfn ${HMM}/sendump -cbdir ${HMM} 2>&1|grep BESTPATH


