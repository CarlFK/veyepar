# -*- mode: ruby -*-
# vi: set ft=ruby :


$script = <<SCRIPT
#!/bin/bash -ex

cp -a /vagrant veyepar 
rm veyepar/dj/scripts/tests.txt
cp veyepar/INSTALL.sh .
./INSTALL.sh 

SCRIPT

VAGRANTFILE_API_VERSION = "2"
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "trusty64"
  config.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"

  config.vm.provision "shell", privileged:false, inline: $script

end
