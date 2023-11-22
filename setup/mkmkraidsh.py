# mkmkraidsh.py
# python script to generage mk_raid.sh


def header():
    print( """
# mk_raid.sh
set -xe

# apt-get install mdadm
    """)

def umount():
    print(f"if [ -d /mnt/space ]; then")
    print(f"  umount /mnt/space")
    print(f"fi")

def remove(md, drives):

    print(f"if [ -f /dev/md{md} ]; then")
    print(f"  mdadm --misc --stop /dev/md{md}")
    print(f"fi")

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
        print(f"mdadm --misc --zero-superblock /dev/sd{d}1")
        # print(f"blockdev --rereadpt /dev/sd{d}")
        print(f"parted /dev/sd{d} --script -- mktable gpt")
        print(f"parted /dev/sd{d} --script -- mkpart primary ext4 0% 100%")
        print(f"parted /dev/sd{d} --script -- print")
        print(f"mdadm --stop --scan")
        print(f"blockdev --rereadpt /dev/sd{d}")
        print()


def mk_md(md, drives):
    cnt = len(drives)
    print( f"mdadm --create /dev/md{md} --level=raid5 --bitmap=internal --raid-devices={cnt} --assume-clean --run \\")
    # print( f"mdadm --create /dev/md{md} --level=raid0 --raid-devices={cnt} --assume-clean \\")
    # print( f"mdadm --create /dev/md{md} --level=faulty --raid-devices={cnt} --assume-clean --run \\")

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
    # print(f"mkfs.ext4 -q /dev/md{md}")
    print(f"mkfs.ext4 -O sparse_super,extent,uninit_bg -E lazy_itable_init=1 -m 0 -q -F /dev/md{md}")
    print(f"e2label /dev/md{md} space")


def conf():
    print(f"mdadm --detail --scan >> /etc/mdadm/mdadm.conf")


def up_initramfs():
    print(f"update-initramfs -u")


def mount():
    print(f"mount /dev/md0 /mnt/space")


def doit():

    md=0
    drives=list("bcde")

    umount()

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

    mount()


def main():
    doit()

if __name__=='__main__':
    main()
