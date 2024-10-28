
TRUE  = 1 # ACK, YES
FALSE = 0 # NAK, NO

from atm import atm

class geni2c (atm): # generic I2C master
    def __init__ (me, busmst, deva, rpt=0):
        me.deva = deva
        me.busmst = busmst # SFR master (I2C)

    def is_master_rdy (me):
        ''' Is this master ready for issuing things?
        '''
        return TRUE if me.busmst else FALSE

    def sfrwx (me, adr, wdat):
        return me.busmst.write (me.deva, adr, wdat)

    def sfrrx (me, adr, cnt):
        return me.busmst.read (me.deva, adr, cnt, FALSE)

    def sfrri (me, adr, cnt):
        ''' Can be improved if the slave support INC mode
        '''
        rdat = []
        for xx in range(cnt):
            rdat += me.busmst.read (me.deva, adr+xx, 1)
        return rdat

    def sfrwi (me, adr, wdat):
        ''' Can be improved if the slave support INC mode
        '''
        ret = 0
        for xx in range(len(wdat)):
            ret += me.busmst.write (me.deva, adr, wdat[xx])
        return ret



from can11xx import can11xx

class cani2c (geni2c, can11xx):
    def __init__ (me, busmst, deva, rpt=0):
        geni2c.__init__ (me, busmst, deva, rpt)
        can11xx.__init__ (me) # SFR target

        if me.sfr.revid:
            if rpt:
                print 'I2C master finds %s, 0x%02x' % (me.sfr.name, me.deva)
            if me.sfr.inc == 1: # CAN1108/11
                me.sfrwx (me.sfr.I2CCTL, [me.sfrrx (me.sfr.I2CCTL,1)[0] | 0x01]) # we'll work in NINC mode



class tsti2c (cani2c, atm):
    pass



from can11xx import can11xx
from cspnvm import *

class tstcsp (can11xx, atm, cspnvm):
    def __init__ (me, busmst, rpt=0):
        me.busmst = busmst # SFR master (canm0)
        super(me.__class__, me).__init__ () # SFR target

        if me.sfr.revid and rpt:
            print 'CSP master finds target %s, %d' % (me.sfr.name, me.busmst.TxOrdrs)


    def is_master_rdy (me):
        ''' Is this master ready for issuing things?
        '''
        return me.busmst.busmst.handle


    def sfrwx (me, adr, wdat):
        return me.busmst.cspw (adr, 1, wdat)


    def sfrwi (me, adr, wdat):
        return me.busmst.cspw (adr, 0, wdat)


    def sfrrx (me, adr, cnt):
        return me.busmst.cspr (adr, 1, cnt)


    def sfrri (me, adr, cnt):
        return me.busmst.cspr (adr, 0, cnt)


    def insert_dummy (me, rawcod, block):
        '''
        insert dummy(s) between each rawcod
        it's better block-sfr.nbyte is a multiple of sfr.nbyte+sfr.dummy
        '''
        lowcod = [] # low byte(s)
        wrcod = []
        for xx in rawcod:                
            if len(lowcod) < me.sfr.nbyte-1:
                lowcod += [xx]
            else:
                # start the program at begin of a block do not need dummy
                for ii in range(me.sfr.dummy):
                    if len(wrcod)%block > 0:
                        wrcod += [0xdd]
                wrcod += lowcod + [xx]
                lowcod = []

        return (len(rawcod), wrcod)


    def calc_csp_prog_block (me):
        """
        calc the optimized block length
        """
        w_unit = (me.sfr.bufsz - me.sfr.nbyte - 2) \
                              / (me.sfr.nbyte + me.sfr.dummy) # CSP command needs 2 bytes
        block = (me.sfr.nbyte + me.sfr.dummy) * w_unit \
               + me.sfr.nbyte # optimize block size by CSP buffer
        return block


    def nvm_prog_block (me, addr, wrcod, rawsz, block=0, hiv=0, note=True):
        """
        override atm's method
        insert dummy byte(s)
        """
        block = me.calc_csp_prog_block () if block==0 else block
        assert block>0 and block<=me.sfr.bufsz, "invalid 'block', %d" % block
        (rawsz, dmycod) = me.insert_dummy (wrcod, block)
        super(me.__class__, me).nvm_prog_block (addr, dmycod, rawsz, block, hiv, note)


    def nvm_block_chk (me, start, expcod, block=32, mismatch=0):
        '''
        limit block size by CSP buffer
        '''
        return \
        super(me.__class__, me).nvm_block_chk (start, expcod, block, mismatch)

