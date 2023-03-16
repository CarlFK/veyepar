# set -ex
host=veyepar.nextdayvideo.com

# ln -s /home/carl/src/dc/debian/ansible dc_a
# ln -s /home/carl/src/dc/debian/ansible/roles/tls-certificates/ ansible/roles/

# hook into debconf-video ansble to use the tls-certificates role
# "By default, Ansible looks for roles in the following locations:...
# * in the configured roles_path. The default search path is ~/.ansible/roles:/usr/share/ansible/roles:/etc/ansible/roles.
# https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_reuse_roles.html#storing-and-finding-roles
# maybe this will work?
a_dir=/usr/share/ansible/roles
dca_dir=${a_dir}/dc_a
if [ -d ${dca_dir} ]; then
    ( cd ${dca_dir}
      git pull
    )
else
    ( cd ${a_dir}
      git clone https://salsa.debian.org/debconf-video-team/ansible dc_a
      ln -l dc_a/roles/tls-certificates
    )
fi

# ansible-playbook ${dca_dir}/site.yml --inventory-file inventory/hosts --user root --limit ${host} -vvv
# --tags streaming,tls-certificates

ansible-playbook ansible/site.yml --inventory-file inventory/hosts --user root --limit ${host} -vvv

