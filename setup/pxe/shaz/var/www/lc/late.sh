# late_command.sh
# touch up the new Ubuntu system

# called from the Ubuntu installer, from this line in the preseed file:
# d-i preseed/late_command  string cd /tmp;apt-get install wget;wget http://shaz/late_command.sh; chmod u+x late_command.sh; chroot /target ./late_command.sh

set -xe
NUSER=@user@

# url=(hostname) of pxe server
# passed from append= in /var/lib/tftpboot/pxelinux.cfg/default 
SHAZ=$url

## ssh greating: cpu, ubuntu ver, firewire guids
# add the cpu name/speed and ubuntu flavor to login greeting
PROFDIR=/etc/profile.d
if [ -d $PROFDIR ]; then
  echo grep -E \"\(name\|MHz\)\" /proc/cpuinfo > $PROFDIR/showcpu.sh 
  echo lsb_release -d -c > $PROFDIR/showrelease.sh 
  echo uname -a > $PROFDIR/showkernel.sh 
  echo cat /sys/devices/virtual/dmi/id/product_name > $PROFDIR/showproduct_name.sh 
  echo cat /sys/bus/firewire/devices/fw?/guid > $PROFDIR/show_fwguid.sh 
  echo "cd /sys/devices/virtual/dmi/id" > $PROFDIR/showproduct_name.sh 
  echo "echo \$(cat sys_vendor) \$(cat product_version) \$(cat product_name)" >> $PROFDIR/showproduct_name.sh 
  echo cd >> $PROFDIR/showproduct_name.sh 
fi

# # beep on firewire card add/remove
cd /etc/udev/rules.d
wget http://$SHAZ/lc/fw-beep.rules


## disable screensaver, blank screen on idle, blank screen on lid close

mkdir -p /etc/dconf/profile
cd /etc/dconf/profile
echo user > user
echo site >> user

mkdir -p /etc/dconf/db/site.d/
mkdir -p /etc/dconf/db/site.d/locks
cd /etc/dconf/db/site.d/

cat <<EOT >local.dconf
[org/gnome/desktop/screensaver]
idle-activation-enabled=false
lock-enabled=false

[org/gnome/desktop/session]
idle-delay=0

[org/gnome/settings-daemon/plugins/power]
lid-close-ac-action='nothing'
lid-close-battery-action='nothing'
idle-dim-ac=false
sleep-display-ac=0
sleep-display-battery=0

[com/ubuntu/update-manager]
check-dist-upgrades=false

[com/canonical/indicator/power]
show-time=true

[com/canonical/indicator/datetime]
show-seconds=true

[org/gnome/desktop/interface]
clock-show-seconds=true

[com/canonical/indicator/datetime]
time-format='24-hour'
show-date=true
show-day=true

EOT
dconf update

## don't check for updates (so no 'UPDATE ME!' dialog.)
CONF=/etc/update-manager/release-upgrades
if [ -f $CONF ]; then
  sed -i "/^Prompt=normal/s/^.*$/Prompt=never/" \
    $CONF
fi

# disable "incomplete language support" dialog
rm -f /var/lib/update-notifier/user.d/incomplete*

CONF=/usr/share/gnome/autostart/libcanberra-login-sound.desktop 
if [ -f $CONF ]; then
  echo X-GNOME-Autostart-enabled=false >> $CONF
fi


# work around bug:
# https://bugs.launchpad.net/ubuntu/+source/gnome-control-center/+bug/792636
# if [ -f /etc/UPower/UPower.conf ]; then
#   sed -i "/^IgnoreLid=false/s/^.*$/IgnoreLid=true/" \
#     /etc/UPower/UPower.conf 
# fi

# this is here till this gets fixed:
# https://launchpad.net/bugs/889656
# debian-installer "installer stops using proxy"

# this bombs the -server install, so screw it.
# apt-get install --assume-yes squid-deb-proxy-client

## enable autologin of $NUSER
# sed docs http://www.opengroup.org/onlinepubs/009695399/utilities/sed.html

# oneiric
CONF=/etc/lightdm/lightdm.conf
if [ -f $CONF ]; then
  printf "autologin-user=%s\n" $NUSER >> $CONF

# natty
elif [ -f /etc/gdm/gdm.conf-custom ]; then
  sed -i \
	 -e '/^\[daemon\]$/aAutomaticLoginEnable=true' \
         -e "/^\[daemon\]$/aAutomaticLogin=$NUSER" \
       /etc/gdm/gdm.conf-custom

# mav?
elif [ -d /etc/gdm ]; then
  CONF=custom.conf
  cat <<EOT >/etc/gdm/$CONF
[daemon]
AutomaticLoginEnable=true
AutomaticLogin=$NUSER
EOT
fi

## remove apt proxy used for install 
# squid-deb-proxy-client has been installed for production 
# Acquire::http::Proxy "http://cp333:8000/";
sed -i "/^Acquire::http::Proxy/s/^.*$//" /etc/apt/apt.conf

## turn off tracker indexing (slows down the box)
if [ -f /home/$NUSER/.config/tracker/tracker.cfg ]; then
  sed -i "/^EnableIndexing=true/s/^.*$/EnableIndexing=false/" \
    /home/$NUSER/.config/tracker/tracker.cfg
fi

## create network manager configs: static ip, dhcp, whacky make up 169 IP
# http://trac.linexa.de/wiki/development/BootCD-booting
# ...Createastaticnetworkmanagerfileforeth0
if [ -d /etc/NetworkManager/system-connections ]; then
 
  get_nm_conf() {
  INI=$1.conf
  wget http://$SHAZ/lc/nm/$INI
  _uuid="$(uuidgen)"
  sed -i "s|@UUID@|${_uuid}|" $INI
  chmod 600 $INI
  }

  cd /etc/NetworkManager/system-connections
  get_nm_conf 10.0.0.1
  get_nm_conf 10.0.0.2
  get_nm_conf 192.168.0.1
  get_nm_conf dhcpipv4
  get_nm_conf auto-magic

fi

## add modules that needs to be added:
## snd-hda-intel sound for HP laptops Intel 82801I (ICH9 Family) HD Audio
# hotplug ec card slot - like firewire cards
cat <<EOT >> /etc/modules
snd-hda-intel
# acpiphp
# pciehp
# yenta_socket
EOT

## grab some home made utilities 
cd /sbin

# APP=async-test
# wget http://$SHAZ/lc/$APP
# chmod 777 $APP 
# chown 1000:1000 $APP 

# rest of script does things in defaunt users home dir (~)
cd /home/$NUSER

# make time command report just total seconds.
printf "\nTIMEFORMAT=%%E\n" >> .bashrc

## create ~/bin

# ~/bin gets added to PATH if it exists when the shell is started.
# so make it now so that it is in PATH when it is needed later. 
mkdir -p bin temp .mplayer
chown 1000:1000 bin temp .mplayer
   
## generic .dvswitchrc, good for testing and production master, slave needs to be tweaked.

cat <<EOT > .dvswitchrc
MIXER_HOST=0.0.0.0
# MIXER_HOST=10.0.0.1
MIXER_PORT=2000
EOT
chown 1000:1000 .dvswitchrc

# APP=x.sh
# echo svn co svn://svn/vga2usb >$APP
# chmod 777 $APP 
# chown 1000:1000 $APP 

APP=x.sh
cat <<EOT > $APP
#!/bin/bash -x
wget -N http://$SHAZ/lc/hook.sh
chmod u+x hook.sh
./hook.sh $1
EOT
chmod 777 $APP
chown 1000:1000 $APP

APP=pxe.py
wget http://$SHAZ/$APP
chmod 777 $APP 
chown 1000:1000 $APP 

## script to install carl's custom dvswitch suite
APP=inst_dvs.sh
cat <<EOT >> $APP
#!/bin/bash -x
# sudo apt-get install python-wxversion
git clone git://github.com/CarlFK/dvsmon.git
sudo apt-add-repository --assume-yes ppa:carlfk
sudo apt-get --assume-yes update
sudo apt-get --assume-yes install dvswitch dvsource dvsink
sudo apt-get --assume-yes install kino
EOT
chmod 777 $APP
chown 1000:1000 $APP
# su -l $NUSER -c "git clone git://github.com/CarlFK/dvsmon.git"


# APP=inst_miro.sh
# cat <<EOT >> $APP
#!/bin/bash -x
# sudo apt-add-repository ppa:pcf/miro-releases
# sudo apt-get update
# sudo apt-get install miro
# miro
# EOT
# chmod 777 $APP
# chown 1000:1000 $APP

## grab Veyepar install script
APP=inst_veyepar.sh
cat <<EOT >> $APP
wget -N http://github.com/CarlFK/veyepar/raw/master/INSTALL.sh 
chmod 777 INSTALL.sh 
./INSTALL.sh 
EOT
chmod 777 $APP 
chown 1000:1000 $APP 

# build melt and all deps
APP=mkmlt.sh
wget http://$SHAZ/lc/$APP
chmod 777 $APP 
chown 1000:1000 $APP 

## get mplayer default config 
APP=.mplayer/config
wget http://$SHAZ/lc/mplayer.conf -O $APP  
chmod 777 $APP 
chown 1000:1000 $APP 

cd bin

## net-console to log kernel errors of some other box
APP=netcons.sh
wget http://$SHAZ/lc/$APP
chmod 777 $APP 
chown 1000:1000 $APP 

cd ..

# APP=slcomp.py
# wget http://$SHAZ/$APP
# chmod 777 $APP 
# chown 1000:1000 $APP 

# wget http://$SHAZ/dvs.tar
# tar xf dvs.tar
# chmod -R 777 dvswitch
# chown -R 1000:1000 dvswitch

# create ~/.ssh, gen private key
# ssh-keygen -f ~/.ssh/id_rsa -N ""

mkdir .ssh
cd .ssh
wget http://$SHAZ/lc/ssh/id_rsa
wget http://$SHAZ/lc/ssh/id_rsa.pub
wget http://$SHAZ/lc/ssh/authorized_keys
wget http://$SHAZ/lc/ssh/config
# wget http://$SHAZ/lc/ssh/known_hosts
chmod 600 config authorized_keys id_rsa
chmod 644 id_rsa.pub 
cd ..
chmod 700 .ssh
chown -R $NUSER:$NUSER .ssh

# add 'private' keys - inscure, they are publicly avalibe on this box.
# cd /home/$NUSER~/.ssh
# wget --overwrite http://$SHAZ/lc/sshkeys.tar
# tar xf sshkeys.tar

# cd sshkeys
# wget -N http://$SHAZ/lc/sshd_config
# cd ..
# cp -f sshkeys/* /etc/ssh
# rm -rf sshkeys sshkeys.tar

## add public keys of people who can log in as $USER
# mkdir .ssh
# chmod -R 700 .ssh
# chown 1000:1000 .ssh
# cd .ssh
# wget http://$SHAZ/lc/authorized_keys
# chmod -R 600 authorized_keys
# chown 1000:1000 authorized_keys
# cd ..


