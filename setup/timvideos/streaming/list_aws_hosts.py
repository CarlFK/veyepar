#!/usr/bin/env python
# -*- coding: utf-8 -*-
# list_aws_hosts.py
# list all active ec2 hosts

"""
Start / stop by name.
Start mission "list_aws_hosts.py start mission"
Stop mission "list_aws_hosts.py stop mission"
Status mission "list_aws_hosts.py status mission"
  mission i-b59966c7 **OFF** stopped
"""

from boto import ec2 
import pw

creds = pw.stream['aws']

def aws_start(instance, name):
    if name == instance.tags['Name']:
        instance.start()

def aws_stop(instance, name):
    if name == instance.tags['Name']:
        instance.stop()

def aws_status(instance, name=None):
    if name and not name == instance.tags['Name']:
        return

    if not instance.dns_name:
        print instance.tags['Name'], instance.id, '**OFF**', instance.state
    else:
        print instance.tags['Name'], instance.id, instance.dns_name, instance.state

def do_command(command, name):
    ec2conn = ec2.connection.EC2Connection(creds['id'], creds['key'])
    reservations = ec2conn.get_all_instances()
    instances = [i for r in reservations for i in r.instances]
    for i in instances:
        command(i, name)

def do_status():
    ec2conn = ec2.connection.EC2Connection(creds['id'], creds['key'])
    reservations = ec2conn.get_all_instances()
    instances = [i for r in reservations for i in r.instances]
    for i in instances:
        aws_status(i)

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 3:
        command, name = sys.argv[1:]
        if command == 'start':
            do_command(aws_start, name)
        elif command == 'stop':
            do_command(aws_stop, name)
        else:
            do_command(aws_status, name)
    else:
        do_status()
