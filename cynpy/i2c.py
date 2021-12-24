
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
    def enum (me): raise NotImplementedError()
    def baud (me, ask): raise NotImplementedError()
    def i2cw (me, wdat): raise NotImplementedError()
    def read (me, dev, adr, rcnt, rpt=FALSE): raise NotImplementedError()

    def write (me, dev, adr, wdat): # SMB write
        return me.i2cw ([dev,adr]+wdat)[1]

    def probe (me):
        print 'Searching I2C slave.....'
        hit = []
        for dev in range(0x80):
            if me.i2cw ([dev]):
                print 'device 0x%02x found' % (dev)
                hit += [dev]
        return hit



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

    i2cmst = choose_master (rpt=TRUE)

    from basic import *
    if not no_argument ():
#       if i2cmst!=0:
            if   sys.argv[1]=='probe' : print i2cmst.probe ()
            elif sys.argv[1]=='baud'  : print i2cmst.baud (argv_dec[2])
            elif sys.argv[1]=='write' : print i2cmst.i2cw (argv_hex[2:])[1]
            elif sys.argv[1]=='read'  : print ['0x%02X' % xx for xx in i2cmst.read (argv_hex[2], argv_hex[3], argv_hex[4])]
            else: print "command not recognized"
#       else: print "I2C master not found"
