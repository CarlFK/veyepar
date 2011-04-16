#!/usr/bin/python 

# dd if=in.dv of=out.dv bs=120000c seek=4538 count=3
# dd if=/home/carl/Videos/veyepar/chipy/april2011/2011-04-14/19:41:44.dv of=out.dv bs=120000c seek=4538 count=3

import optparse

def dv_slice(o,a):

    f_in = open(o.in_name, 'rb')
    f_out = open(o.out_name,'wb')

    start_byte = o.start * o.bpf
    count_bytes = o.count * o.bpf
    end_byte = start_byte + count_bytes
    if o.verbose:
        print "start: %s count: %s end: %s" % (
                start_byte, count_bytes, end_byte )
    f_in.seek(start_byte)
    while o.count:
        f_out.write(f_in.read(o.bpf))
        o.count -= 1

    f_in.close()
    f_out.close()


def parse_args():
    parser = optparse.OptionParser()
    parser.set_defaults(bpf=120000)
    parser.set_defaults(start=0)
    parser.set_defaults(count=1)
    parser.set_defaults(in_name='in.dv')
    parser.set_defaults(out_name='out.dv')

    parser.add_option('--bpf', type=int,
            help="bytes per frame", )
    parser.add_option('--start', type=int,
            help="start frame", )
    parser.add_option('--count', type=int,
            help="start frame", )
    parser.add_option('--in-name',
            help="in_name", )
    parser.add_option('--out-name',
            help="out_name", )
    parser.add_option('-v', '--verbose', action='store_true')

    options, args = parser.parse_args()
    return options,args

if __name__ == '__main__':
    opts, args = parse_args()
    dv_slice(opts,args)
    
