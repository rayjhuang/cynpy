
from cansfr import *

class can11xx (object):
    '''
    can11xx hierarchy
    -----------------                                     canm0
                                                   {sfr  /
                                                   updrpl - ams
                                            {i2c  /            |
            sfr1108                         cani2c - tsti2c   ~ isp
           /                               /        /
    sfr11xx - sfr111x - sfr1110  }  can11xx      atm 
                     \                     \        \
                      sfr1112                - - - - tstcsp   ~ csp
                                                    /  {canm0
                                              cspnvm
    '''
    def __init__ (me):
        me.sfr = sfr11xx() # initial
        if me.is_master_rdy():
            revid = me.get_revid ()
#           print 'master is ready', revid
            if revid > 0: # found
                if sfr1108().check (revid): me.sfr = sfr1108(revid)
                if sfr1110().check (revid): me.sfr = sfr1110(revid)
                if sfr1112().check (revid): me.sfr = sfr1112(revid)
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



class sfr (object):
    """
    to monitor I2C/CSP register
    to save read/modify time on communication channel
    """

    def __init__ (me, sfrmst, port, val=-1, dbmsg=FALSE):
        me.p = port # port/address
        me.v = [0] # one element for recovering
        me.sfrmst = sfrmst
        me.d = dbmsg
        if val<0: me.v[0] = me.sfrmst.sfrrx (port, 1)[0] # initial condition
        else:     me.v[0] = val                          # power-on value

    def __del__ (me):
        '''
        DIFFICULT TO CONTROL THIS
        SO THIS RECOVERY FUNCTION DOESN'T WORK YET
        '''
#       me.set (me, me.v[0])
        print 'SFR.%02X died' % (me.p)

    def doit (me):
        me.sfrmst.sfrwx (me.p, [me.v[-1]]) # main job of this class
        if me.d:
            print 'SFR.%02X: %02X, [' % (me.p,me.v[-1]), \
                  '%02X ' * len(me.v) % tuple(me.v)

    def get (me): return me.v[-1]

    def set (me, val, force=FALSE): # to set without push
        assert val==(val&0xff), '"val" out of range'
        chk = me.v[-1] != val
        me.v[-1] = val 
        if force or chk:
            me.doit ()

    def psh (me, val=-1, force=FALSE):
        if val<0:
            me.v += [ me.v[-1] ] # duplicate
        else:
            assert val==(val&0xff), '"val" out of range'
            me.v += [ val ] # push
            if force or me.v[-1] != me.v[-2]:
                me.doit ()

    def pop (me, force=FALSE): # resume
        tmp = me.v.pop ()
        if force or me.v[-1] != tmp:
            me.doit ()

    def msk (me, a, o=0):
        me.psh ((me.v[-1] & a) | o)
