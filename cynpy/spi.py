
from aardvark_py import *
from aardv import aardvark_spi
import time

class spinvm (aardvark_spi):

    PAGE_SIZE = 32

    def block32_erase (me, adr): # 32KB-block
        me.spix ([0x06]) # Send write enable command
        me.spix ([0x52, \
                 (adr >> 16) & 0xff, (adr >> 8) & 0xff, adr & 0xff]) # Send sector erase command
        time.sleep(800/1000)

    def sector_erase (me, adr): # 4KB-sector
        me.spix ([0x06]) # Send write enable command
        me.spix ([0x20, \
                 (adr >> 16) & 0xff, (adr >> 8) & 0xff, adr & 0xff]) # Send sector erase command
        time.sleep(400/1000)

    def page_program (me, adr, wdat): # 256-byte page
        n = 0
        length = len(wdat)
        while (n < length):
            me.spix ([0x06]) # Send write enable command

            data_out = [ 0x02, \
                         (adr >> 16) & 0xff, (adr >> 8) & 0xff, adr & 0xff ] + \
                       [ 0 for i in range(me.PAGE_SIZE) ] # Assemble write command and address
            i = 4
            while 1: # Assemble a page of data
                data_out[i] = wdat[n]
                adr = adr + 1
                n = n + 1
                i = i + 1
                if not (n < length and (adr & (me.PAGE_SIZE-1)) ): break

            del data_out[i:] # Truncate the array to the exact data size
            me.spix (data_out) # Write the transaction
            aa_sleep_ms(5)

    def page_read (me, adr, sz):
        data_in = []
        for adr in range(adr,adr+sz,me.PAGE_SIZE):
            page = sz if (adr+me.PAGE_SIZE > sz) else me.PAGE_SIZE
            data_in = data_in + me.read (0x03, adr, page)
            aa_sleep_ms(5)
        return data_in

    def dump (me, adr, sz):
        data_in = me.page_read (adr, sz)
        for i in range(len(data_in)): # Dump the data to the screen
            if ((i&0x0f) == 0):
                sys.stdout.write("\n%04x:  " % (adr+i))
            sys.stdout.write("%02x " % (data_in[i] & 0xff))
            if (((i+1)&0x07) == 0):
                sys.stdout.write(" ")
        sys.stdout.write("\n")

    def upload (me, binfile):
        print binfile
        start = time.time ()
        f = 0
        lines = []
        if binfile[-4:].lower() == '.bin':
            f = open(binfile,'rb')
            lines = map(ord,list(f.read()))

        me.page_program (0, lines)
        print '%.1f sec' % (time.time () - start)
        print len(lines), 'bytes'

    def download (me, binfile, sz=0x2000):
        start = time.time ()
        dncode = me.page_read (0,sz)
        print len(dncode), 'bytes'
        f = open(binfile,'wb')
        if f:
            print binfile
            f.write(''.join(chr(e) for e in dncode))
            f.close()
        else:
            print 'ERROR: file open'
        print '%.1f sec' % (time.time () - start)



if __name__ == '__main__':

    from basic import *
    if not no_argument ():
        if   sys.argv[1]=='ver'    : spinvm(0).aaShowVersion ()
        elif sys.argv[1]=='dump'   : spinvm(0).dump (argv_hex[2],argv_hex[3])
        elif sys.argv[1]=='erase'  : spinvm(0).sector_erase (argv_hex[2])
        elif sys.argv[1]=='upload' : spinvm(0).upload (sys.argv[2])
        elif sys.argv[1]=='dnload' : spinvm(0).download (sys.argv[2])
        elif sys.argv[1]=='prog'   : spinvm(0).page_program (argv_hex[2],argv_dec[3],argv_dec[4])
        else: print "command not recognized"
