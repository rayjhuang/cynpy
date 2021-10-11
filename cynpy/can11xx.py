
from cansfr import *

class can11xx (object):
    '''
    can11xx hierarchy
    -----------------                                     canm0
                                                   {sfr  /
                                                   updrpl - ams ~ ~
                                            {i2c  /               |
            sfr1108                         cani2c - - - tsti2c   ~ isp
           /                               /            /
    sfr11xx - sfr111x - sfr1110  }  can11xx    nvm - atm 
                     \                     \            \
                      sfr1112                - - - - - - tstcsp   ~ csp
                                                        /  {canm0
                                                  cspnvm
    '''
    def __init__ (me):
        me.sfr = sfr11xx() # initial
        if me.is_master_rdy():
            revid = me.get_revid ()
#           print 'master is ready', revid
            if revid > 0: # found
                if   sfr1108().check (revid): me.sfr = sfr1108(revid)
                elif sfr1110().check (revid): me.sfr = sfr1110(revid)
                elif sfr1112().check (revid): me.sfr = sfr1112(revid)
                elif sfr1124().check (revid): me.sfr = sfr1124(revid)
                else:
                    print 'un-recognized REVID: %02X' % revid
                    me.sfr = sfr11xx()
#       else:
#           print 'master is not ready'


    def is_master_rdy (me): raise NotImplementedError()

    def sfrwx (me, adr, wdat): raise NotImplementedError() # non-INC write
    def sfrwi (me, adr, wdat): raise NotImplementedError() # INC write

    def sfrrx (me, adr, cnt): raise NotImplementedError() # non-INC read
    def sfrri (me, adr, cnt): raise NotImplementedError() # INC read


    def get_revid (me):
        sav = me.sfrrx (me.sfr.DEC, 1) # try slave
        if len(sav): # data returned
            me.sfrwx (me.sfr.DEC, [me.sfr.REVID])
            revid = \
            me.sfrrx (me.sfr.REVID, 1)[0] & 0x7f
            me.sfrwx (me.sfr.DEC, [sav[0]])
            return revid
        return 0



class cani2c (can11xx):
    def __init__ (me, busmst, deva, rpt=0):
        me.deva = deva
        me.busmst = busmst # SFR master (I2C)

        can11xx.__init__ (me) # SFR target

        if me.sfr.revid:
            if rpt:
                print 'I2C master finds %s, 0x%02x' % (me.sfr.name, me.deva)
            if me.sfr.inc == 1: # CAN1108/11
                me.sfrwx (me.sfr.I2CCTL, [me.sfrrx (me.sfr.I2CCTL,1)[0] | 0x01]) # we'll work in NINC mode


    def is_master_rdy (me):
        ''' Is this master ready for issuing things?
        '''
        return TRUE if me.busmst else FALSE


    def sfrwx (me, adr, wdat):
        return me.busmst.write (me.deva, adr, wdat)


    def sfrrx (me, adr, cnt):
        return me.busmst.read (me.deva, adr, cnt, FALSE)


    def sfrri (me, adr, cnt):
        sav = me.sfrrx (me.sfr.I2CCTL, 1)[0]
        setinc = sav & 0xfe if me.sfr.inc else sav | 0x01
        me.sfrwx (me.sfr.I2CCTL, [setinc]) # INC mode
        rdat = me.busmst.read (me.deva, adr, cnt)
        me.sfrwx (me.sfr.I2CCTL, [sav])
        return rdat

    def sfrwi (me, adr, wdat):
        sav = me.sfrrx (me.sfr.I2CCTL, 1)[0]
        setinc = sav & 0xfe if me.sfr.inc else sav | 0x01
        me.sfrwx (me.sfr.I2CCTL, [setinc]) # INC mode
        ret = me.busmst.write (me.deva, adr, wdat)
        me.sfrwx (me.sfr.I2CCTL, [sav])
        return ret

