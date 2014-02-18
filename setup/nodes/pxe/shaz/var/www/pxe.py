#!/usr/bin/python

import subprocess
import os.path
import optparse 


def shell(cmd):
    
    sh = open('pxe.sh','a')
    if isinstance(cmd,list):
        s=' '.join(cmd)
        print s
        sh.writelines(s)
    else:
        print cmd
        sh.writelines(cmd)
        cmd = cmd.split()
    sh.write('\n')
    print cmd

    return subprocess.Popen(cmd)

def tftpget(server, filename=''):
    """ tftp get a file """
    print "get %s %s..." % (server,filename)
    open('pxe.sh','a').write('tftp %s  <<< "get %s"\n' % (server,filename))
    try:
        ftpget = subprocess.Popen(['tftp', server], stdin=subprocess.PIPE,stdout=subprocess.PIPE); 
    except OSError:    
    	shell('sudo apt-get install tftp kexec-tools').wait()
        ftpget = subprocess.Popen(['tftp', server], stdin=subprocess.PIPE,stdout=subprocess.PIPE); 
    (stdout, stderr) = ftpget.communicate('get %s' % (filename))
    print stdout, stderr

def getdefault(server):
    tftpget(server, 'pxelinux.cfg/default')
    # read file from disk, parse into lines
    default=open('default').read().split('\n')
    return default

def get_labels(server, filt=''):
    default=getdefault(server)
    lables=[]
    for l in default:
        if l:
            parts=l.split()
            print parts
            if parts[0]=='label' and filt.lower() in parts[1].lower():
                lables.append(parts[1]) 
    return lables

def dump(server, filt=''):
    for l in get_labels(server, filt):
        print l

def puke(server,label):
    default=getdefault(server)
    d={}
    o=default.index('label %s' % (label))
    for line in default[o:o+3]:
        lline = line.split()
        print lline,
        key,value=lline[0].lower(),lline[1:]
        if key=='append':
            # look for 'initrd=' in all the append parameters
            orgval=value
            value=[]
            for a in orgval:
                la = a.split('=')
                if la[0]=='initrd':
                    d['initrd']=la[1]
                else:
                    # everything else goes back into the append line
                    value.append(a)   
            # look for 'initrd=' in all the append parameters
            for a in value:
                la = a.split('=')
                if la[0]=='initrd':
                    d['initrd']=la[1]

        d[key]=' '.join(value)
    return d

def kexec(d,run=False):
    shell('sudo service gdm stop')
    shell('sudo service lightdm stop')
    shell('sudo /etc/init.d/gdm stop')
    kexec= [ 'sudo', 'kexec', 
        '--load', os.path.basename(d['linux']),
        '--initrd=%s' % os.path.basename(d['initrd']),
        '--append=%s' % d['append'],
        ]
    shell(kexec)
    print ' '.join(kexec)
    cmd= 'sudo kexec --console-vga --reset-vga --exec'
    print cmd
    open('pxe.sh','a').write(cmd)
    if run: shell(cmd)

def qemu(d):

    # apt-get install qemu-kvm kvm-pxe
    # qemu-img create -f qcow2 hda.qcow2 5G

    # hack to fix lack of search=
    d['append']=d['append'].replace('shaz','shaz.personnelware.com')
    qemu = [ 'qemu', 
        '-hda', 'hda.qcow2',
        '-net', 'nic', '-net', 'user,hostname=qemu',
        '-kernel', os.path.basename(d['linux']),
        '-initrd',  os.path.basename(d['initrd']),
        '-append', d['append'],
        ]
    shell(qemu)

def boot(label,options):

    # parse default, spit out a dict of what we want: 
    d = puke(options.server,label)
    print d

    # for carl's ubuntu installs, taylor what gets installed
    if options.flavor:
        print options.flavor
        d['append']=d['append'].replace( 
            'ubuntu-standard, ubuntu-desktop', 
            {'x': 'ubuntu-standard, xubuntu-desktop', 
            'y': 'ubuntu-standard, mythbuntu-desktop', 
            's': '', }[options.flavor] )

    # get the kernel and initrd
    tftpget(options.server, d['linux'])
    tftpget(options.server, d['initrd'])
    
    # execute:
    if options.qemu:
        qemu(d)
    else: 
        kexec(d,options.kexec)


def parse_args():
    parser = optparse.OptionParser()

    parser.add_option('-s', "--server",
        default='trist',
        help="pxe server", )
    parser.add_option("-l", "--list",
        action="store_true", default=False,
        help="list labels", )
    parser.add_option("-f", "--flavor",
        choices=['x','y','s'],
        help="x=xubuntu, y=mythbuntu, s=server", )
    parser.add_option("-q", "--qemu",
        action="store_true", default=False,
        help="run in Qemu", )
    parser.add_option( "--kexec",
        action="store_true", default=False,
        help="really run kexec", )

    options, args = parser.parse_args()
    return options, args


def main():
    options, args = parse_args()

    if options.list or not args:
        if args:
            dump( options.server, args[0] )
        else:
            dump( options.server )
    else:
    	shell('sudo apt-get install tftp kexec-tools').wait()
        boot(args[0],options)

if __name__ == '__main__':
    main()

