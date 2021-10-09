
from cynpy.can11xx import cani2c
from cynpy.atm import atm

class tsti2c (cani2c, atm):
    pass



from cynpy.can11xx import can11xx
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
        load the memory file 'memfile' and insert dummys
        '''
        lowcod = [] # low-byte
        wrcod = []
        for xx in rawcod:                
            if len(lowcod)>0 or me.sfr.nbyte==1:
                if len(wrcod)%block > 0:
                    for yy in range(me.sfr.dummy):
                        wrcod += [0xdd]
                wrcod += lowcod + [xx]
                lowcod = []
            else:
                lowcod = [xx]

        return (len(rawcod), wrcod)


    def calc_cspnvm_block (me):
        """
        calc. block length
        """
        w_unit = (me.sfr.bufsz - me.sfr.nbyte - 2) \
                              / (me.sfr.nbyte + me.sfr.dummy) # CSP command needs 2 bytes
        block = (me.sfr.nbyte + me.sfr.dummy) * w_unit \
               + me.sfr.nbyte # optimize block size by CSP buffer
        return block

        
    def nvm_prog_raw_block (me, wrcod):
        """
        override atm's method
        Single-Mode0-Write transaction
        """
        print wrcod
        (rawsz, dmycod) = me.insert_dummy (wrcod, me.calc_cspnvm_block ())
        print (rawsz, dmycod)
        super(me.__class__, me).nvm_prog_raw_block (dmycod)


    def nvm_prog_block (me, addr, wrcod, rawsz, hiv=0):
        """
        override atm's method
        insert dummy byte(s)
        """
        block = me.calc_cspnvm_block ()
        (rawsz, dmycod) = me.insert_dummy (wrcod, block)
        super(me.__class__, me).nvm_prog_block (addr, dmycod, rawsz, hiv, block)


    def nvm_block_chk (me, start, expcod, mismatch=0, block=32):
        '''
        limit block size by CSP buffer
        '''
        return \
        super(me.__class__, me).nvm_block_chk (start, expcod, mismatch, block)


    def nvm_comp_block (me, addr, expcod, block=32, blank_check=0):
        '''
        limit block size by CSP buffer
        '''
        super(me.__class__, me).nvm_comp_block (addr, expcod, block, blank_check)
