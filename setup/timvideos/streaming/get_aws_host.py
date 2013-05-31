import boto
import pw

id='i-b59966c7' # misson
id='i-5dba412f' # america
id='i-45ba4137' # cd
id='i-e8a4a39b' # www

creds = pw.stream['aws']
ec2 = boto.connect_ec2( creds['id'], creds['key'] )
hostname = ec2.get_all_instances(instance_ids=[id])[0].instances[0].public_dns_name

print hostname

