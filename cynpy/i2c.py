
TRUE  = 1 # ACK, YES
FALSE = 0 # NAK, NO

class i2c (object): # for polymorphism
    '''
    i2c class hierarchy
    -------------------
         i2c
             \
               aardvark_i2c
             / (aardv.py)
    aardvark
    
    '''
    def enum (me):        raise NotImplementedError()
    def baud (me, ask=0): raise NotImplementedError()
    def i2cw (me, wdat):  raise NotImplementedError()
    def read (me, dev, adr, rcnt, rpt=FALSE):
                          raise NotImplementedError()

    def write (me, dev, cmd, wdat): # SMB write
        return me.i2cw ([dev,cmd]+wdat)[1]

    def probe (me):
        print 'Searching I2C slave.....'
        hit = []
        for dev in range(0x80):
            if me.i2cw ([dev])==(0,0): # aa_i2c_write_ext returns
                print 'device 0x%02x found' % (dev)
                hit += [dev]
        return hit

    def test (me, dev, cmd):
        print 'I2C pattern for measurement.....'
        me.read (dev, cmd, 1)
        me.read (dev, cmd, 1)
        me.write (dev, cmd, [3])


def choose_master (rpt=FALSE):
    '''
    TO CONSIDER FOLLOWING SCENARIOS
    -------------------------------
    1. use AARDARK in a non-Windows system
    '''
    from aardv import aardvark_i2c as aa_i2c
    num = aa_i2c().enum (rpt)
    return aa_i2c(0) # i2cmst



if __name__ == '__main__':

    import sys
    def i2c_dispatch (tstmst):
        rtn = sys.argv[1]
        if   sys.argv[1]=='enum'  : pass # not for CCF
        elif sys.argv[1]=='probe' : print i2cmst.probe ()
        elif sys.argv[1]=='baud'  : print i2cmst.baud (cmd.argv_dec[2]) if len(sys.argv)>2 else i2cmst.baud ()
        elif sys.argv[1]=='i2cw'  : print i2cmst.i2cw (cmd.argv_hex[2:])[1]
        elif sys.argv[1]=='i2cr'  : print ['0x%02X' % xx for xx in \
                                    i2cmst.read (cmd.argv_hex[2], cmd.argv_hex[3], cmd.argv_hex[4])]
        elif sys.argv[1]=='read' or \
             sys.argv[1]=='write' or \
             sys.argv[1]=='loopw' or \
             sys.argv[1]=='loopwr' or \
             sys.argv[1]=='loopr1' or \
             sys.argv[1]=='loopr2' or \
             sys.argv[1]=='scope_sfr' or \
             sys.argv[1]=='d' or \
             sys.argv[1]=='dump'  : cmd.basic_dispatch (tstmst)   # used in CCF
        elif sys.argv[1]=='deva'  : tstmst.deva = cmd.argv_hex[2] # used in CCF
        elif sys.argv[1]=='test'  : i2cmst.test (cmd.argv_hex[2], cmd.argv_hex[3])
        else: rtn = 'none'
        return rtn

    import basic as cmd
    if cmd.chk_argument ():
        i2cmst = choose_master (rpt = TRUE if 'enum'==sys.argv[1] else FALSE)
        if i2cmst:
            deva = 0x70 # default for can11xx
            assign = sys.argv[1].split('=')
            if len(assign)==2:
                if assign[0]=='deva': deva = int(assign[1],16)
                cmd.pop_argument ()
            import sfrmst
            tstmst = sfrmst.geni2c (busmst=i2cmst, deva=deva)
            cmd.tstmst_func (tstmst, i2c_dispatch)
        else:
            print "I2C master not found"

        i2cmst.__del__()
