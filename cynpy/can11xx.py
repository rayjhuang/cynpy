
from cansfr import *

class can11xx (object):
    '''
    can11xx hierarchy
    -----------------                                     canm0
                                {i2c               {sfr  /
                                generic_i2c        updrpl - ams ~ ~
                                           \      /               |
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
#           print 'master is ready, 0x%02x' % revid
            if revid > 0: # found
                if   sfr1108().check (revid): me.sfr = sfr1108(revid)
                elif sfr1110().check (revid): me.sfr = sfr1110(revid)
                elif sfr1112().check (revid): me.sfr = sfr1112(revid)
                elif sfr1123().check (revid): me.sfr = sfr1123(revid)
                elif sfr1124().check (revid): me.sfr = sfr1124(revid)
                elif sfr1125().check (revid): me.sfr = sfr1125(revid)
                else:
                    print 'un-recognized REVID: 0x%02x' % revid
            else:
                print 'ERROR: REVID not found'
#       else:
#           print 'ERROR: master is not ready'


    def is_master_rdy (me): raise NotImplementedError()

    def sfrwx (me, adr, wdat): raise NotImplementedError() # non-INC write
    def sfrwi (me, adr, wdat): raise NotImplementedError() # INC write

    def sfrrx (me, adr, cnt): raise NotImplementedError() # non-INC read
    def sfrri (me, adr, cnt): raise NotImplementedError() # INC read


    def get_revid (me):
        sav = me.sfrrx (me.sfr.DEC, 1) # try slave
#       sav = [] # don't try-slave
        if len(sav): # data returned
            me.sfrwx (me.sfr.DEC, [me.sfr.REVID])
            revid = \
            me.sfrrx (me.sfr.REVID, 1)[0] & 0x7f
            me.sfrwx (me.sfr.DEC, [sav[0]])
            return revid
        else:
            print 'ERROR: no data returned'
            return 0

