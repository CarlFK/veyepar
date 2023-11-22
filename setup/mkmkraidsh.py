# mkmkraidsh.py
# python script to generage mk_raid.sh

def header():
    print( """
# mk_raid.sh
set -xe

# apt-get install mdadm
    """)

def remove(md, drives):

    print( f"mdadm --misc --stop /dev/md{md}")

    """
    cnt = len(drives)

    print( f"mdadm --remove /dev/md{md} --force --raid-devices={cnt} \\" )
    print( "  ", end="" )
    for d in drives:
        print( f"/dev/sd{d}1", end=" ")
    print()
    """
    print()

def stop():
    print( """
/etc/init.d/mdadm stop
/etc/init.d/udev stop
    """ )

def scan():
    print( """
mdadm --stop --scan
    """ )

def mk_parts(md, drives):
    for d in drives:
        print(f"blockdev --rereadpt /dev/sd{d}")
        print(f"parted /dev/sd{d} --script -- mktable gpt")
        print(f"parted /dev/sd{d} --script -- mkpart primary ext4 0% 100%")
        print(f"parted /dev/sd{d} --script -- print")
        print(f"mdadm --stop --scan")
        print(f"blockdev --rereadpt /dev/sd{d}")
        print()


def mk_md(md, drives):
    cnt = len(drives)
    print( f"mdadm --create /dev/md{md} --level=raid10 --bitmap=internal --raid-devices={cnt} --assume-clean \\")
    for d in drives:
        print( f"/dev/sd{d}1", end=" ")
    print( "  ", end="" )
    print()
    print()


def start():
    print("/etc/init.d/mdadm start")
    print("/etc/init.d/udev start")
    print("# above line may be erroring, which aborts the script?")


def mkfs(md):
    print(f"mkfs.ext4 /dev/md{md}")
    print(f"e2label /dev/md{md} space")


def conf():
    print(f"mdadm --detail --scan >> /etc/mdadm/mdadm.conf")


def up_initramfs():
    print(f"update-initramfs -u")


def doit():

    md=0
    drives=list("bcde")

    header()
    remove(md, drives)
    stop()
    scan()
    mk_parts(md, drives)
    scan()
    mk_md(md, drives)
    start()
    mkfs(md)
    conf()
    up_initramfs()


"""

# show us what we got
# (well, as much as I know how to show - some sort of grub setup would be nice.)

"""

def main():
    doit()

if __name__=='__main__':
    main()
