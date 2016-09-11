# late_command.sh

# called from the Ubuntu installer, from this line in the preseed file:
# d-i preseed/late_command string cd /target/tmp && wget http://$url/lc/late.sh && chmod u+x late.sh && chroot /target /tmp/late.sh $(debconf-get mirror/suite) $(debconf-get passwd/username)

set -x

suite=$1 # oneiric, saucy, trusty, utopic, vivid, wily
nuser=$2 # juser

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

  # echo "cd /sys/devices/virtual/dmi/id" > $PROFDIR/showproduct_name.sh 
  # echo "echo \$(cat sys_vendor) \$(cat product_version) \$(cat product_name)" >> $PROFDIR/showproduct_name.sh 
  # echo cd >> $PROFDIR/showproduct_name.sh 

  cat <<EOT > $PROFDIR/showproduct_name.sh 
cd /sys/devices/virtual/dmi/id
echo \$(cat sys_vendor) \$(cat product_version) \$(cat product_name)
cd
EOT

  cat <<EOT > $PROFDIR/show_fwguid.sh
if [ -d /sys/bus/firewire/devices/ ]; then
  echo
  find /sys/bus/firewire/devices/ -name "fw?" -exec printf "{} " \; -exec cat {}/guid \;
  echo
fi
EOT

fi

# # beep on firewire card add/remove
cd /etc/udev/rules.d
wget http://$SHAZ/lc/fw-beep.rules
cd

## disable screensaver, blank screen on idle, blank screen on lid close
# https://wiki.gnome.org/action/show/Projects/dconf/SystemAdministrators
# gconftool-2 --direct --config-source=xml:readwrite:/etc/gconf/gconf.xml.defaults --type bool --set /apps/gnome-screensaver/idle_activation_enabled false

mkdir -p /etc/dconf/db/site.d/locks
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
case $suite in
  percise)
  rm -f /var/lib/update-notifier/user.d/incomplete*
  ;;
esac


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

# update ipxe (fixes bug with hp laptops) (maybe)
cd /boot
rm ipxe.efi
wget -N http://boot.ipxe.org/ipxe.lkrn

## enable autologin of $nuser
# sed docs http://www.opengroup.org/onlinepubs/009695399/utilities/sed.html

case $suite in
  trusty|utopic|vivid|wily|xenial)
  CONF=/etc/lightdm
  if [ -d $CONF ]; then
    cd $CONF
    mkdir lightdm.conf.d
    cd lightdm.conf.d
    cat <<EOT > 12-autologin.conf
[SeatDefaults]
autologin-user=$nuser
EOT
  fi ;;
  oneiric | precise)
  CONF=/etc/lightdm/lightdm.conf
  if [ -f $CONF ]; then
    printf "autologin-user=%s\n" $nuser >> $CONF
  fi ;;
  natty)
  sed -i \
	 -e '/^\[daemon\]$/aAutomaticLoginEnable=true' \
         -e "/^\[daemon\]$/aAutomaticLogin=$nuser" \
       /etc/gdm/gdm.conf-custom
  ;; 
  maveric)
  cat <<EOT >/etc/gdm/custom.conf
[daemon]
AutomaticLoginEnable=true
AutomaticLogin=$nuser
EOT
;;
esac

# install here and not 
# d-i pkgsel/include string squid-deb-proxy-client
# https://launchpad.net/bugs/889656
# debian-installer "installer stops using proxy"

# apt-get install --force-yes --assume-yes \
# 	squid-deb-proxy-client

## remove apt proxy used for install 
# squid-deb-proxy-client has been installed for production 
# Acquire::http::Proxy "http://cp333:8000/";
CONF=/etc/apt/apt.conf
if [ -f $CONF ]; then
  sed -i "/^Acquire::http::Proxy/s/^.*$//" $CONF 
fi

## turn off tracker indexing (slows down the box)
CONF=/home/$nuser/.config/tracker/tracker.cfg
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
  get_nm_conf eyes

fi

cat <<EOT >> /etc/exports
# /home/$nuser/Videos  192.168.1.0/16(rw,async,no_subtree_check)
# /home/$nuser/Videos  10.0.0.1/32(rw,async,no_subtree_check)
/home/$nuser/Videos  room100.local(rw,async,no_subtree_check)
EOT

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
# chown $nuser:$nuser $APP 

# rest of script does things in defaunt users home dir (~)
cd /home/$nuser

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
chown -R $nuser:$nuser .ssh

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
# chown $nuser:$nuser .ssh
# cd .ssh
# wget http://$SHAZ/lc/authorized_keys
# chmod -R 600 authorized_keys
# chown $nuser:$nuser authorized_keys
# cd ..


# make time command report just total seconds.
printf "\nTIMEFORMAT=%%E\n" >> .bashrc
printf "\nexport DISPLAY=:0.0\n" >> .bashrc


## create ~/bin
# ~/bin gets added to PATH if it exists when the shell is started.
# so make it now so that it is in PATH when it is needed later. 
mkdir -p bin temp .mplayer .config/autostart .config/conky
chown -R $nuser:$nuser bin temp .mplayer .config 

cd .config/autostart
wget http://$SHAZ/lc/conky/conky.desktop
chown $nuser:$nuser conky.desktop
cd ../conky
wget http://$SHAZ/lc/conky/conkyrc
chown $nuser:$nuser conkyrc

cd /home/$nuser

## generic .dvswitchrc, good for testing and production master, slave needs to be tweaked.

cat <<EOT > .dvswitchrc
MIXER_HOST=10.0.0.1
# MIXER_HOST=room_100.local
# MIXER_HOST=mixer.local
# MIXER_HOST=192.168.0.1
# MIXER_HOST=0.0.0.0
MIXER_PORT=2000
EOT
chown -R $nuser:$nuser .dvswitchrc

cat <<EOT > veyepar.cfg
[global]
client=test_client
show=test_show
room=test_loc
upload_formats=mp4 
EOT
chown -R $nuser:$nuser veyepar.cfg


cat <<EOT > .voctomix.ini 
[mix]
videocaps=video/x-raw,format=I420,width=1280,height=720,framerate=30000/1001,pixel-aspect-ratio=1/1
sources=cam1,grabber

[mainvideo]
playaudio=true

[previews]
enabled=false
videocaps=video/x-raw,width=1280,height=720,framerate=30000/1001

[videodisplay]
# system=gl
# system=xv
# system=x

EOT
chown -R $nuser:$nuser .voctomix.ini 

fn=.minirc.dfl
cat <<EOT > $fn
pu port             /dev/ttyACM0
pu addcarreturn     Yes
EOT
chown -R $nuser:$nuser $fl


# echo svn co svn://svn/vga2usb >$APP
# chmod 777 $APP 
# chown $nuser:$nuser $APP 

APP=x.sh
cat <<EOT > $APP
#!/bin/bash -x
wget -N http://$SHAZ/lc/hook.sh
chmod u+x hook.sh
./hook.sh \$*
EOT
chmod 744 $APP
chown $nuser:$nuser $APP

APP=pxe.py
wget http://$SHAZ/$APP
chmod 744 $APP 
chown $nuser:$nuser $APP 

## script to install analog clock
APP=inst_clocky.sh
cat <<EOT >> $APP
#!/bin/bash -x
# sudo apt-get install python-wxgtk2.8
git clone git://github.com/CarlFK/clocky.git
EOT
chmod 744 $APP
chown $nuser:$nuser $APP


## script to install carl's custom dvswitch suite
APP=inst_dvs.sh
cat <<EOT >> $APP
#!/bin/bash -x
# sudo apt-get install python-wxgtk2.8
# git clone git://github.com/CarlFK/dvsmon.git
# sudo apt-add-repository --yes ppa:carlfk
# sudo apt-get --assume-yes update
# sudo apt-get --assume-yes install dvswitch dvsource dvsink
EOT
chmod 744 $APP
chown $nuser:$nuser $APP

## Veyepar install script
APP=inst_veyepar.sh
cat <<EOT >> $APP
wget -N http://github.com/CarlFK/veyepar/raw/master/INSTALL.sh 
chmod u+x INSTALL.sh 
./INSTALL.sh 
EOT
chmod 744 $APP 
chown $nuser:$nuser $APP 

## vocto  
APP=inst_vocto.sh
cat <<EOT >> $APP
#!/bin/bash -ex
git clone https://github.com/voc/voctomix.git

git clone git://github.com/CarlFK/voctomix-outcasts.git
git clone git://github.com/CarlFK/dvsmon.git

cd ~/bin

ln -s ~/voctomix/voctocore/voctocore.py voctocore
ln -s ~/voctomix/voctogui/voctogui.py voctogui

ln -s ~/voctomix-outcasts/ingest.py ingest

ln -s ~/voctomix-outcasts/record-timestamp.sh record-timestamp
ln -s ~/voctomix-outcasts/record-mixed-av.sh record-mixed-av
ln -s ~/voctomix-outcasts/generate-cut-list.py generate-cut-list

EOT
chmod 744 $APP 
chown $nuser:$nuser $APP 

# I wonder if this will work?
# ./$APP
# chown -R $nuser:$nuser voctomix voctomix-outcasts dvsmon



## gst-uninstalled  
APP=mk_gst.sh
cat <<EOT >> $APP
#!/bin/bash -ex
# http://arunraghavan.net/2014/07/quick-start-guide-to-gst-uninstalled-1-x/
sudo apt-get build-dep gstreamer1.0-plugins-{base,good,bad,ugly}
curl https://cgit.freedesktop.org/gstreamer/gstreamer/plain/scripts/create-uninstalled-setup.sh | sh
ln -sf ~/gst/master/gstreamer/scripts/gst-uninstalled ~/bin/gst-master
gst-master ./gstreamer/scripts/git-update.sh
EOT
chmod 744 $APP 
chown $nuser:$nuser $APP 

sudo apt-get build-dep gstreamer1.0-plugins-{base,good,bad,ugly,libav}

# https://www.blackmagicdesign.com/support/family/capture-and-playback
mkdir blackmagic; cd blackmagic
wget http://$SHAZ/lc/bm/desktopvideo_10.6.8a2_amd64.deb .
dpkg -i desktopvideo_10.6.8a2_amd64.deb
# wget http://$SHAZ/lc/bm/Blackmagic_Desktop_Video_Linux_10.6.8.tar.gz
# tar xvf Blackmagic_Desktop_Video_Linux_10.6.8.tar.gz
# cd Blackmagic_Desktop_Video_Linux_10.6.8/deb/amd64/

cd /home/$nuser


## get mplayer default config 
APP=.mplayer/config
wget http://$SHAZ/lc/mplayer.conf -O $APP  
chmod 744 $APP 
chown $nuser:$nuser $APP 

cd bin
ln -s /home/$nuser/local/Shotcut/Shotcut.app/melt

cd ..

cd Desktop
# logo loop for shows
# APP=pyohio_2014_logos.odp
# wget http://$SHAZ/lc/$APP
# chown $nuser:$nuser $APP 

cd ..

cd temp

APP=fix_grub.sh
wget http://$SHAZ/lc/$APP  
chmod 744 $APP 
chown $nuser:$nuser $APP 

cd ..

