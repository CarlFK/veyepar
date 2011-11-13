#!/bin/bash -x

# sets up kernel message loggig to a netconsole server like ncc.py
# or 
# netcat -u -l -p 6666
# add a tee to log to disk.
# but ncc.py is better.

NETCONSLOGR=shaz
printf "start %s %s %s\n" $(hostname) $(date --rfc-3339=ns)| netcat -q 1 -u $NETCONSLOGR 6666
sudo modprobe netconsole netconsole="@/,@$NETCONSLOGR/"

