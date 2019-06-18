
from aardvark_py import *
from aardv import aardvark_spi

class spinvm (aardvark_spi):

    PAGE_SIZE = 32

    def block32_erase (me, adr): # 32KB-block
        me.spix ([0x06]) # Send write enable command
        me.spix ([0x52, \
                 (adr >> 16) & 0xff, (adr >> 8) & 0xff, adr & 0xff]) # Send sector erase command
        aa_sleep_ms(800)

    def sector_erase (me, adr): # 4KB-sector
        me.spix ([0x06]) # Send write enable command
        me.spix ([0x20, \
                 (adr >> 16) & 0xff, (adr >> 8) & 0xff, adr & 0xff]) # Send sector erase command
        aa_sleep_ms(400)

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

    def dump (me, adr, length):
        data_in = me.read (0x03, adr, length)
        for i in range(len(data_in)): # Dump the data to the screen
            if ((i&0x0f) == 0):
                sys.stdout.write("\n%04x:  " % (adr+i))
            sys.stdout.write("%02x " % (data_in[i] & 0xff))
            if (((i+1)&0x07) == 0):
                sys.stdout.write(" ")
        sys.stdout.write("\n")

    def upload (me, memfile):
        print memfile
        f = 0
        lines = []
        if memfile[-4:].lower() == '.bin':
            f = open(memfile,'rb')
            lines = map(ord,list(f.read()))

        me.page_program (0,lines)



if __name__ == '__main__':

    from basic import *
    if not no_argument ():
        if   sys.argv[1]=='ver'    : spinvm(0).aaShowVersion ()
        elif sys.argv[1]=='dump'   : spinvm(0).dump (argv_hex[2],argv_hex[3])
        elif sys.argv[1]=='erase'  : spinvm(0).sector_erase (argv_hex[2])
        elif sys.argv[1]=='upload' : spinvm(0).upload (sys.argv[2])
        elif sys.argv[1]=='prog'   : spinvm(0).page_program (argv_hex[2],argv_dec[3],argv_dec[4])
        else: print "command not recognized"
