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

def aws_start(instance, *names):
    if names and instance.tags['Name'] in names:
        instance.start()

def aws_stop(instance, *names):
    if names and instance.tags['Name'] in names:
        instance.stop()

def aws_status(instance, *names):
    if names and instance.tags['Name'] not in names:
        return

    if not instance.dns_name:
        print instance.tags['Name'], instance.id, '**OFF**', instance.state
    else:
        print instance.tags['Name'], instance.id, instance.dns_name, instance.state

def do_command(command, *names):
    ec2conn = ec2.connection.EC2Connection(creds['id'], creds['key'])
    reservations = ec2conn.get_all_instances()
    instances = [i for r in reservations for i in r.instances]
    for i in instances:
        command(i, *names)

def do_status():
    ec2conn = ec2.connection.EC2Connection(creds['id'], creds['key'])
    reservations = ec2conn.get_all_instances()
    instances = [i for r in reservations for i in r.instances]
    for i in instances:
        aws_status(i)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('command', help='command to run', nargs='?', default='status', choices=['start', 'stop', 'status'])
    parser.add_argument('name', help='AWS instance names (set as a tag Name)', nargs='*')
    args = parser.parse_args()
    commands = {'start': aws_start, 'stop': aws_stop, 'status': aws_status}
    if len(args.name):
        do_command(commands[args.command], *args.name)
    elif args.command is 'status':
        do_status()
    else:
        parser.print_help()
