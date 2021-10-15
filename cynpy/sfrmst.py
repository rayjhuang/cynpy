
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

