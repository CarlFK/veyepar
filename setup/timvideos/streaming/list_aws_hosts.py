# list_aws_hosts.py
# list all active ec2 hosts

from boto import ec2 
import pw

creds = pw.stream['aws']

ec2conn = ec2.connection.EC2Connection(creds['id'], creds['key'] )
reservations = ec2conn.get_all_instances()
instances = [i for r in reservations for i in r.instances]
for i in instances:
    if not i.dns_name:
        continue
    print i.tags['Name'], i.id, i.dns_name
