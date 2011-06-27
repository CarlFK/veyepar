#!/usr/bin/python

import datetime
import csv
import StringIO
import pprint 

# seconds from midnight, timestamp, bytes sent
log="""56521.93324, 2011-06-24 15:42:01.933240, 0
56521.933569, 2011-06-24 15:42:01.933569, 1292
56521.933722, 2011-06-24 15:42:01.933722, 1488
56522.022575, 2011-06-24 15:42:02.022575, 16488
56522.023069, 2011-06-24 15:42:02.023069, 31488
56522.03704, 2011-06-24 15:42:02.037040, 46488
56522.079995, 2011-06-24 15:42:02.079995, 61488
56522.080119, 2011-06-24 15:42:02.080119, 76488
56522.116328, 2011-06-24 15:42:02.116328, 91488"""


reader = csv.reader(open('uploadlog.csv', 'rb'))
# reader = csv.reader(StringIO.StringIO(log))

i=0
dat = []
last_sec = 0
for row in reader:
    sec=float(row[0])
    bytes_sent = int(row[2])
    if last_sec: 
        timestamp = datetime.datetime.strptime(row[1],' %Y-%m-%d %H:%M:%S.%f')
        duration=sec - last_sec
        chunk = bytes_sent - last_bytes 
        bps = chunk/duration
        dat.append( [sec-first_sec, chunk, duration, bps, timestamp] )
    else:
        first_sec = float(row[0])

    last_sec = sec
    last_bytes = bytes_sent

    if sec-first_sec > 30: break

# pprint.pprint(dat)

# seconds from first log entry,
# bytes sent for that entry,
# seconds to send those bytes
# bps (bytes/seconds)
"""
[[0.00032900000223889947, 1292, 0.00032900000223889947, 3927051.645008286],
 [0.00048200000310316682, 196, 0.00015300000086426735, 1281045.7443976079],
 [0.089335000004211906, 15000, 0.08885300000110874, 168818.16033012758],
 [0.089829000004101545, 15000, 0.00049399999988963827, 30364372.476419158],
 [0.10380000000441214, 15000, 0.013971000000310596, 1073652.5660057638],
 [0.14675500000157626, 15000, 0.042954999997164123, 349202.65396322421],
 [0.14687899999989895, 15000, 0.00012399999832268804, 120967743.57177937],
 [0.18308799999795156, 15000, 0.036208999998052604, 414261.6476789398]]
"""

xys = [ (int(row[0]*10000),int(row[3])) for row in dat ]
# pprint.pprint( xys )


import os, tempfile, random, cStringIO
os.environ['MPLCONfigureDIR'] = tempfile.mkdtemp()
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

def plot(title='title',xlab='x',ylab='y',
        data={'xxx':[(0,0),(1,1),(1,2),(3,3)],
              'yyy':[(0,0,.2),(2,1,0.2),(2,2,0.2),(3,3,0.2)]},
               filename='test.png'):
   figure=Figure(frameon=False)
   axes=figure.add_subplot(111)
   if title: axes.set_title(title)
   if xlab: axes.set_xlabel(xlab)
   if ylab: axes.set_ylabel(ylab)
   keys=sorted(data)
   for key in keys:
       stream = data[key]
       (x,y)=([],[])
       for point in stream:
           x.append(point[0])
           y.append(point[1])
       axes.plot(x, y, linewidth="2")
   canvas=FigureCanvas(figure)
   stream=open(filename,'wb')
   canvas.print_png(stream)

points=[(3, 3927051), (4, 1281045), (893, 168818),]
# plot(data={'mypoints':points},filename='test.png')
plot(data={'mypoints':xys},filename='test.png')

