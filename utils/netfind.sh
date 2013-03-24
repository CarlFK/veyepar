#!/bin/bash -x

for i in `nmap -p 22 10.1.1.0/24 | grep 10.1.1 | sed -e 's/Nmap scan report for //'`; do 
    echo $i
    ssh $i locate local_settings.py
done
