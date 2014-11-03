# late_command.sh

# called from the Ubuntu installer, from this line in the preseed file:
# d-i preseed/late_command string cd /target/tmp && wget http://$url/lc/late.sh && chmod u+x late.sh && chroot /target /tmp/late.sh $(debconf-get mirror/suite) $(debconf-get passwd/username)

set -x

SUITE=$1 # saucy, trusty
NUSER=$2

# url=(hostname) of pxe server
# passed from append= in /var/lib/tftpboot/pxelinux.cfg/default 
SHAZ=$url

## ssh greating: cpu, ubuntu ver, firewire guids
# add the cpu name/speed and ubuntu flavor to login greeting
PROFDIR=/etc/profile.d
if [ -d $PROFDIR ]; then
  echo grep -E \"\(name\|MHz\)\" /proc/cpuinfo > $PROFDIR/showcpu.sh 
  echo lsb_release --short --description --codename > $PROFDIR/showrelease.sh 
  echo uname -a > $PROFDIR/showkernel.sh 
  # echo cat /sys/bus/firewire/devices/fw?/guid > $PROFDIR/show_fwguid.sh 

cat <<EOT >$PROFDIR/show_fwguid.sh
echo
find /sys/bus/firewire/devices/ -name "fw?" -exec printf "{} " \; -exec cat {}/guid \;
echo
EOT

  echo "cd /sys/devices/virtual/dmi/id" > $PROFDIR/showproduct_name.sh 
  echo "echo \$(cat sys_vendor) \$(cat product_version) \$(cat product_name)" >> $PROFDIR/showproduct_name.sh 
  echo cd >> $PROFDIR/showproduct_name.sh 

fi

# # beep on firewire card add/remove
cd /etc/udev/rules.d
wget http://$SHAZ/lc/fw-beep.rules
cd

## disable screensaver, blank screen on idle, blank screen on lid close
mkdir -p /etc/dconf/profile
cd /etc/dconf/profile
cat <<EOT >user
user-db:user
system-db:site
EOT

mkdir -p /etc/dconf/db/site.d/
cd /etc/dconf/db/site.d/

cat <<EOT >20-recording-mixer
[org/gnome/desktop/screensaver]
idle-activation-enabled=false
lock-enabled=false

[org/gnome/desktop/session]
idle-delay=uint32 0

[org/gnome/settings-daemon/plugins/power]
lid-close-ac-action='nothing'
lid-close-battery-action='nothing'
idle-dim-ac=false
idle-dim=false
sleep-display-ac=uint32 0
sleep-display-battery=uint32 0

[com/ubuntu/update-manager]
check-dist-upgrades=false

[com/canonical/indicator/power]
show-time=true

[com/canonical/indicator/datetime]
show-date=true
show-day=true
time-format='24-hour'
show-locations=true
show-seconds=true

[org/gnome/desktop/interface]
clock-show-seconds=true

EOT
dconf update


## don't check for updates (so no 'UPDATE ME!' dialog.)
CONF=/etc/update-manager/release-upgrades
if [ -f $CONF ]; then
  sed -i "/^Prompt=normal/s/^.*$/Prompt=never/" $CONF
fi

# disable "incomplete language support" dialog
# rm -f /var/lib/update-notifier/user.d/incomplete*

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

# wget http://mirrors.us.kernel.org/ubuntu//pool/universe/i/ipxe/grub-ipxe_1.0.0+git-4.d6b0b76-0ubuntu2_all.deb
# there is some problem with this right now, so pfft.
# something to do with needing pxe.  I bed I need to use gdebi?
# dpkg -i grub-ipxe_1.0.0+git-4.d6b0b76-0ubuntu2_all.deb


## enable autologin of $NUSER
# sed docs http://www.opengroup.org/onlinepubs/009695399/utilities/sed.html

if [ "$SUITE" = "trusty" ]; then
  CONF=/etc/lightdm
  if [ -d $CONF ]; then
    cd $CONF
    mkdir lightdm.conf.d
    cd lightdm.conf.d
    cat <<EOT > 12-autologin.conf
[SeatDefaults]
autologin-user=$NUSER
EOT
  fi

elif [ "$SUITE" = "oneiric" ]; then
  CONF=/etc/lightdm/lightdm.conf
  if [ -f $CONF ]; then
    printf "autologin-user=%s\n" $NUSER >> $CONF
  fi 

elif [ "$SUITE" = "natty" ]; then
  sed -i \
	 -e '/^\[daemon\]$/aAutomaticLoginEnable=true' \
         -e "/^\[daemon\]$/aAutomaticLogin=$NUSER" \
       /etc/gdm/gdm.conf-custom

elif [ "$SUITE" = "maveric" ]; then
  cat <<EOT >/etc/gdm/custom.conf
[daemon]
AutomaticLoginEnable=true
AutomaticLogin=$NUSER
EOT

fi

# install here and not 
# d-i pkgsel/include string squid-deb-proxy-client
# https://launchpad.net/bugs/889656
# debian-installer "installer stops using proxy"

apt-get install --force-yes --assume-yes \
	squid-deb-proxy-client

## remove apt proxy used for install 
# squid-deb-proxy-client has been installed for production 
# Acquire::http::Proxy "http://cp333:8000/";
CONF=/etc/apt/apt.conf
if [ -f $CONF ]; then
  sed -i "/^Acquire::http::Proxy/s/^.*$//" $CONF 
fi

## turn off tracker indexing (slows down the box)
CONF=/home/$NUSER/.config/tracker/tracker.cfg
if [ -f $CONF ]; then
  sed -i "/^EnableIndexing=true/s/^.*$/EnableIndexing=false/" $CONF
fi

## create network manager configs: static ip, dhcp, whacky make up 169 IP
# http://trac.linexa.de/wiki/development/BootCD-booting
# ...Createastaticnetworkmanagerfileforeth0
CONF=/etc/NetworkManager/system-connections
if [ -d $CONF ]; then
 
  get_nm_conf() {
  INI=$1.conf
  wget http://$SHAZ/lc/nm/$INI
  _uuid="$(uuidgen)"
  sed -i "s|@UUID@|${_uuid}|" $INI
  chmod 600 $INI
  }

  cd $CONF
  get_nm_conf 10.0.0.1
  get_nm_conf 10.0.0.2
  get_nm_conf 192.168.0.1
  get_nm_conf dhcpipv4
  get_nm_conf auto-magic

fi

## add modules that needs to be added:
cat <<EOT >> /etc/modules
## snd-hda-intel sound for HP laptops Intel 82801I (ICH9 Family) HD Audio
# snd-hda-intel
# hotplug ec card slot - like firewire cards
# acpiphp
# pciehp
# yenta_socket
EOT

## grab some home made utilities 
# cd /sbin
# APP=async-test
# wget http://$SHAZ/lc/$APP
# chmod 777 $APP 
# chown $NUSER:$NUSER $APP 

# rest of script does things in defaunt users home dir (~)
cd /home/$NUSER

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
# chown $NUSER:$NUSER .ssh
# cd .ssh
# wget http://$SHAZ/lc/authorized_keys
# chmod -R 600 authorized_keys
# chown $NUSER:$NUSER authorized_keys
# cd ..


# make time command report just total seconds.
printf "\nTIMEFORMAT=%%E\n" >> .bashrc

## create ~/bin
# ~/bin gets added to PATH if it exists when the shell is started.
# so make it now so that it is in PATH when it is needed later. 
mkdir -p bin temp .mplayer
chown -R $NUSER:$NUSER bin temp .mplayer
   
## generic .dvswitchrc, good for testing and production master, slave needs to be tweaked.

cat <<EOT > .dvswitchrc
MIXER_HOST=0.0.0.0
# MIXER_HOST=10.0.0.1
# MIXER_HOST=192.168.0.1
MIXER_PORT=2000
EOT
chown -R $NUSER:$NUSER .dvswitchrc

# APP=x.sh
# echo svn co svn://svn/vga2usb >$APP
# chmod 777 $APP 
# chown $NUSER:$NUSER $APP 

APP=x.sh
cat <<EOT > $APP
#!/bin/bash -x
wget -N http://$SHAZ/lc/hook.sh
chmod u+x hook.sh
./hook.sh \$1
EOT
chmod 744 $APP
chown $NUSER:$NUSER $APP

APP=pxe.py
wget http://$SHAZ/$APP
chmod 744 $APP 
chown $NUSER:$NUSER $APP 

## script to install carl's custom dvswitch suite
APP=inst_dvs.sh
cat <<EOT >> $APP
#!/bin/bash -x
sudo apt-get install python-wxgtk2.8

git clone git://github.com/CarlFK/dvsmon.git
sudo apt-add-repository --enable-source --yes ppa:carlfk
sudo apt-get --assume-yes update
sudo apt-get --assume-yes install dvswitch dvsource dvsink
exit
sudo apt-get install libav-dbg libglib2.0-0-dbg libglibmm-2.4-dbg libgtk2.0-0-dbg
sudo apt-get build-dep dvswitch
apt-get source dvswitch
cd dvswitch-0.9.2/
export DEB_BUILD_OPTIONS=nostrip,noopt
dpkg-buildpackage
sudo dpkg -i ../dvswitch_0.9.2-1ubuntu2_amd64.deb

EOT
chmod 744 $APP
chown $NUSER:$NUSER $APP

## Veyepar install script
APP=inst_veyepar.sh
cat <<EOT >> $APP
wget -N http://github.com/CarlFK/veyepar/raw/master/INSTALL.sh 
chmod u+x INSTALL.sh 
./INSTALL.sh 
EOT
chmod 744 $APP 
chown $NUSER:$NUSER $APP 

## grab gst-switch  install-test script
# chain this script to wget install.sh so that we get the latest version 
APP=inst_gst-switch-test.sh
cat <<EOT >> $APP
#!/bin/bash -ex
wget -N https://raw.github.com/hyades/gst-switch/master/scripts/install.sh 
chmod u+x install.sh 
sudo apt-add-repository "deb http://archive.ubuntu.com/ubuntu precise universe"
sudo apt-add-repository "deb http://archive.ubuntu.com/ubuntu precise multiverse"
sudo apt-add-repository "deb http://archive.ubuntu.com/ubuntu $SUITE universe"
sudo apt-add-repository "deb http://archive.ubuntu.com/ubuntu $SUITE multiverse"
sudo apt-add-repository universe
sudo apt-add-repository multiverse
./install.sh 
EOT
chmod 744 $APP 
chown $NUSER:$NUSER $APP 


# build melt and all deps
# APP=mkmlt.sh
# wget http://$SHAZ/lc/$APP
# wget -N http://github.com/CarlFK/veyepar/raw/master/setup/nodes/encode/$APP 
# chmod 744 $APP 
# chown $NUSER:$NUSER $APP 

## get mplayer default config 
APP=.mplayer/config
wget http://$SHAZ/lc/mplayer.conf -O $APP  
chmod 744 $APP 
chown $NUSER:$NUSER $APP 

cd bin

## net-console to log kernel errors of some other box
APP=netcons.sh
wget http://$SHAZ/lc/$APP
chmod 744 $APP 
chown $NUSER:$NUSER $APP 

cd ..

# APP=slcomp.py
# wget http://$SHAZ/$APP
# chmod 744 $APP 
# chown $NUSER:$NUSER $APP 

# wget http://$SHAZ/dvs.tar
# tar xf dvs.tar
# chmod -R 744 dvswitch
# chown -R $NUSER:$NUSER dvswitch

