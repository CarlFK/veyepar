# cpl.sh
# copy logs - and configs, scripts, etc.
set -x
if [ -z "$1" ]
then
	echo "No target dir passed."
	echo $0 "<target dir>"
	exit
fi

#DEST=/tmp/misc/installer_logs/$(cat /etc/hostname)
HOSTNAME=$(cat /etc/hostname)
DEST=/tmp/misc/installer_logs/$HOSTNAME
mkdir -p $DEST

# get the URL of the preeseed from url='URL'
PRESEEDURL=$(set|grep ^url=|sed "s#\(^url='\)\(.*\)\('\)#\2#")
# get the URL of the pxe boot parameters  
DEFAULTURL=$(echo $DEFAULTURL|sed -e 's#^\(http://[^/]*/\).*$#\1#')default

cat >$DEST/README<<EOF
The files in this tree are from the alternate installer environment.
To see how they were collected, see the $0 script (which generated 
this README file.) 

Typically (but not always) the installer was booted from a pxe/tftp 
server.  See the file named 'default' for the boot paramaters likely used 
for this instalation attempt.  A good clue will be to find the one that 
specifies the preseed file used: $PRESEEDURL
EOF

# wget -P $DEST $(set|grep ^preseed|sed "s/\(^.*'\)\(.*\)\('\)/\2/")
wget -P $DEST $PRESEEDURL
wget -P $DEST $DEFAULTURL

dmesg >$DEST/dmesg.txt 
ps >$DEST/ps.txt 
set>$DEST/set.txt
lspci >$DEST/lcpci.txt 
fdisk -l >$DEST/fdisk.txt 2>&1
sfdisk --list >$DEST/sfdisk.txt 2>&1
dmraid -c -s >$DEST/dmraid.txt 2>&1
cat /proc/partitions >$DEST/partitions.txt 2>&1
cat /proc/mdstat >$DEST/mdstat.txt 2>&1

mkdir -p $DEST/target/var
ln -s /target/var/log $DEST/target/var/
ln -s /etc $DEST
ln -s /var/log $DEST
cp early_command.sh $DEST
cp $0 $DEST

cd $DEST/..
# tar -czvf install_logs.tgz $DEST
# tar: invalid option -- 'c'
# Usage: tar -[zxtvO] [-f TARFILE] [-C DIR] [FILE(s)]...
# (02:43:20 PM) cjwatson: debian/config/config.udeb:# CONFIG_FEATURE_TAR_CREATE is not set

# send to web server's temp dir, tar it and make it readable.
scp -r $DEST carl@dev.personnelware.com:$1
# ssh carl@dev.personnelware.com tar czvf $1/install_logs_${HOSTNAME}_$1.tgz $1/$HOSTNAME
# ssh carl@dev.personnelware.com chmod -R o+r $1
