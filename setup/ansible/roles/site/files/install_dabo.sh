#!/bin/sh -ex

vdir=$1

# Installs Dabo into the python virtualenv site-packages
# elample: /home/videoteam/vipar/dj/venv/lib/python3.9/site-packages
# virtualenv dir is passed as the $1 parameter

cd $(${vdir}/bin/python3 -c "import sysconfig; print( sysconfig.get_path('purelib'))")
if [ ! -d dabo-master ]; then
    git clone --branch dabo3 --single-branch https://github.com/CarlFK/dabo.git dabo-master
fi
ln -s dabo-master/dabo
touch /home/videoteam/dabo_installed.txt

