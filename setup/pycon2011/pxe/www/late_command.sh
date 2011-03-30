# late_command.sh
# touch up the new Ubuntu system

# called from the Ubuntu installer, from this line in the preseed file:
# d-i preseed/late_command  string cd /tmp;apt-get install wget;wget http://shaz/late_command.sh; chmod u+x late_command.sh; ./late_command.sh

set -xe
TARGET=/target
# NUSER=videoteam
NUSER=juser
# NUSER=carl

SHAZ=192.168.2.1

# have dhcp client send the hostname
# fiesty now does it - yay!
# Hardy doesn't.  boo!
# jaunty does, yay!
# echo send host-name \"$(cat $TARGET/etc/hostname)\"\;  >> $TARGET/etc/dhcp3/dhclient.conf
# echo send host-name \"\<hostname\>\"\;  >> $TARGET/etc/dhcp3/dhclient.conf

# add the cpu name/speed and ubuntu flavor to login greeting
PROFDIR=$TARGET/etc/profile.d
if [ -d $PROFDIR ]; then
  echo grep -E \"\(name\|MHz\)\" /proc/cpuinfo > $PROFDIR/showcpu.sh 
  echo lsb_release -d -c > $PROFDIR/showrelease.sh 
fi

# setup some fstab entries and create the mount pointss

# add a module that needs to be added:
# hotplug ec card slot - like firewire cards
cat <<EOT >> $TARGET/etc/modules
acpiphp
EOT

# cat <<EOT >> $TARGET/etc/fstab
# 192.168.1.3:/video/data1 /video nfs soft,auto,user,defaults 0 0 
# EOT

# mkdir -p $TARGET/mnt/nfs/cw1b/carl
# mkdir -p $TARGET/video

# for vga2usb device control app v2u...
# echo \# usbfs /proc/bus/usb usbfs auto 0 0 >> $TARGET/etc/fstab
# echo \# none /dev/shm tmpfs rw,size=144m >> $TARGET/etc/fstab

# make firewire device readable by video group
# for reading dv cam over firewire
cat <<EOT >> $TARGET/etc/udev/rules.d/91-permissions.rules
# ieee1394 devices
KERNEL=="raw1394",    GROUP="video"
EOT

# turn off tracker indexing (slows down the box)
if [ -f $TARGET/home/$NUSER/.config/tracker/tracker.cfg ]; then
  sed -i "/^EnableIndexing=true/s/^.*$/EnableIndexing=false/" \
    $TARGET/home/$NUSER/.config/tracker/tracker.cfg
fi


if [ -f $TARGET/usr/bin/gconftool-2 ]; then
  # disable screensaver, blank screen on idle, blank screen 
  # gconf-editor (to figure out what to set..)
  chroot $TARGET gconftool-2 --direct --config-source=xml:readwrite:/etc/gconf/gconf.xml.defaults --type bool --set /apps/gnome-screensaver/idle_activation_enabled false
  chroot $TARGET gconftool-2 --direct --config-source=xml:readwrite:/etc/gconf/gconf.xml.defaults --type int --set /apps/gnome-power-manager/timeout/sleep_display_ac 0
  chroot $TARGET gconftool-2 --direct --config-source=xml:readwrite:/etc/gconf/gconf.xml.defaults --type string --set /apps/gnome-power-manager/buttons/lid_ac blank
  chroot $TARGET gconftool-2 --direct --config-source=xml:readwrite:/etc/gconf/gconf.xml.defaults --type bool --set /apps/gnome-power-manager/backlight/battery_reduce false
  chroot $TARGET gconftool-2 --direct --config-source=xml:readwrite:/etc/gconf/gconf.xml.defaults --type bool --set /apps/gnome-power-manager/backlight/enable false
  chroot $TARGET gconftool-2 --direct --config-source=xml:readwrite:/etc/gconf/gconf.xml.defaults --type bool --set /apps/gnome-power-manager/backlight/idle_dim_battery false

  # this doesn;t work - but it just creates a shortcut to term, c-a-t works better anyway.
  # chroot $TARGET GCONF_CONFIG_SOURCE="xml:readwrite:/etc/gconf/gconf.xml.defaults" /usr/lib/gnome-panel/gnome-panel-add  --launcher /usr/share/applications/gnome-terminal.desktop --panel=top_panel_screen0

#  chroot $TARGET 

fi

# enable autologin of $NUSER
# sed docs http://www.opengroup.org/onlinepubs/009695399/utilities/sed.html

CONF=gdm.conf-custom
if [ -f $TARGET/etc/gdm/$CONF ]; then
  sed -i \
	 -e '/^\[daemon\]$/aAutomaticLoginEnable=true' \
         -e "/^\[daemon\]$/aAutomaticLogin=$NUSER" \
       $TARGET/etc/gdm/$CONF

elif [ -d $TARGET/etc/gdm ]; then
  CONF=custom.conf
  cat <<EOT >$TARGET/etc/gdm/$CONF
[daemon]
AutomaticLoginEnable=true
AutomaticLogin=$NUSER
EOT
fi

# touch up /grub/menu.lst 
# sed -i "/^# defoptions=quiet splash/s/^.*$/# defoptions=vga=6/" $TARGET/boot/grub/menu.lst
# in-target update-grub
# TODO: work with  grub2

# remove proxy used for install 
# squid-deb-proxy-client has been installed for production 
# Acquire::http::Proxy "http://cp333:8000/";
sed -i "/^Acquire::http::Proxy/s/^.*$//" $TARGET/etc/apt/apt.conf

# work flow server
cat <<EOT >$TARGET/etc/hosts
192.168.2.1	wfs
EOT

# rest of script does things in defaunt users home dir (~)
cd $TARGET/home/$NUSER

# ~/bin gets added to PATH if it exists when the shell is started.
# so make it now so that it is in PATH when it is needed later. 
mkdir bin temp
chown 1000:1000 bin temp
   
cat <<EOT > .dvswitchrc
MIXER_HOST=0.0.0.0
MIXER_PORT=2000
EOT
chown 1000:1000 .dvswitchrc

APP=x.sh
echo svn co svn://svn/vga2usb >$APP
chmod 777 $APP 
chown 1000:1000 $APP 

APP=pxe.py
wget http://$SHAZ/$APP
chmod 777 $APP 
chown 1000:1000 $APP 

APP=inst_dvs.sh
cat <<EOT >> $APP
#!/bin/bash -x
git clone git://github.com/CarlFK/dvsmon.git
sudo apt-add-repository ppa:carlfk
sudo apt-get update
sudo apt-get install dvswitch dvsource dvsink
EOT
chmod 777 $APP 
chown 1000:1000 $APP 


APP=inst_veyepar.sh
echo wget -N --no-check-certificate https://github.com/CarlFK/veyepar/raw/master/INSTALL.sh >$APP
echo chmod 777 INSTALL.sh >> $APP 
echo ./INSTALL.sh >> $APP 
chmod 777 $APP 
chown 1000:1000 $APP 

APP=inst_hook.sh
cat <<EOT >> $APP
#!/bin/bash -x
wget http://192.168.2.1/hook.sh
chmod 777 hook.sh
./hook.sh
EOT
chmod 777 $APP 
chown 1000:1000 $APP 


cd bin
APP=netcons.sh
wget http://$SHAZ/$APP
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

# add private keys - inscure.
# wget http://$SHAZ/sshkeys.tar
# tar xf sshkeys.tar
# cd sshkeys
# wget http://$SHAZ/sshd_config
# cd ..
# cp -f sshkeys/* $TARGET/etc/ssh

# add public keys of people who can log in as $USER
mkdir .ssh
chmod -R 700 .ssh
chown 1000:1000 .ssh
cd .ssh
wget http://$SHAZ/authorized_keys
chmod -R 600 authorized_keys
chown 1000:1000 authorized_keys
cd ..

# grab some scripts, make them +x, but don't execure them.
# cd $TARGET/root
# wget http://$SHAZ/cpl.sh 
# chmod u+x cpl.sh 
# wget http://$SHAZ/getdabo.sh
# chmod u+x getdabo.sh 
# wget http://$SHAZ/testdabo.sh
# chmod u+x testdabo.sh 

