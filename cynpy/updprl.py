
from can11xx import cani2c, TRUE, FALSE

class updprl (cani2c):
    '''
    base class of ams and canm0
    '''
    OrdrsType = ['NA','SOP','SOP\'','SOP"','SOP\'_Debug','SOP"_Debug','Hard Reset','Cable Reset']
    CtrlMsg = ['Rsvd0','GoodCRC','GotoMin','Accept','Reject','Ping','PS_RDY','Get_Source_Cap', \
               'Get_Sink_Cap','DR_Swap','PR_Swap','VCONN_Swap','Wait','Soft_Reset','Rsvd14','Rsvd15']
    DataMsg = ['Rsvd0','Source_Capabilities','Request','BIST','Sink_Capabilities','Battery_Status','Alert','Get_Country_Info', \
               'Rsvd8','Rsvd9','Rsvd10','Rsvd11','Rsvd12','Rsvd13','Rsvd14','Vendor_Defined']


    def __init__ (me, i2cmst, deva, ordrs=0):
        '''
        don't enable auto-TX-GoodCRC initially
            1. for Mode0 doesn't need
            2. keep silence when DUT speaks
        enable all ordrs RX for SOP* query
        '''
        me.MyMsgId = 0
        me.DataRole = 0 # reserved (shall be 0) in SOP'/SOP"
        me.PortRole = 0 # 0/1: SOP(sink/source), SOP'SOP"(port/cable)
        me.SpecRev = 1 # PD_R2
        me.Vconn = 0 # 0/1: VCONN sink/source
        me.TxOrdrs = ordrs & 0x07

        me.TxBuffer = []

        super(updprl, me).__init__ (i2cmst, deva)

        me.prltx = sfr(me, me.sfr.PRLTX, -1)
        me.txctl = sfr(me, me.sfr.TXCTL, -1, TRUE)

        me.sfrwx (me.sfr.RXCTL,[0x7f])


    def ordered_set (me, hr):
        me.txctl.psh (0x48) # disable SOP/EOP, enable encode K-code
        ordrs = [0x55,0x65] if hr else [0x15,0x35] # RST-1,RST-1, RST-1,RST-2  : Hard Reset
        me.sfrwx (me.sfr.FFCTL,[0x40]) # first     # RST-1,Sync-1,RST-1,Sync-3 : Cable Reset
        me.sfrwx (me.sfr.FFSTA,[0x00]) # clear FIFO
        me.sfrwx (me.sfr.STA1, [0xff]) # clear STA1
        me.sfrwx (me.sfr.FFIO, [ordrs[0]])
        me.sfrwx (me.sfr.FFCTL,[0x82]) # last, 2-byte K-code
        me.sfrwx (me.sfr.FFIO, [ordrs[1]])
        sta1 = me.sfrrx (me.sfr.STA1,1)[0]
        if (sta1&0x30)==0x10: print 'ORDRS = %s' % ('CableReset','HardReset')[hr]
        else:                 print "--- DISCARDED ---, %02X"%sta1
        me.txctl.pop()


    def compose_msg (me, msgtype, DO=[]):
        '''
        construct message and send
        DO is 32-bit
        return FALSE if discarded
        '''
        NDO = len(DO)
        me.TxBuffer = \
                [(   msgtype &0x1f) | ((me.DataRole&0x01) <<5) | ((me.SpecRev&0x03) <<6), \
                 (me.PortRole&0x01) | ((me.MyMsgId &0x07) <<1) | ((   NDO    &0x07) <<4)]
        for xx in range(NDO):
            me.TxBuffer += [(DO[xx])    &0xff, \
                            (DO[xx]>>8) &0xff, \
                            (DO[xx]>>16)&0xff, \
                            (DO[xx]>>24)&0xff ]

        me.sfrwx (me.sfr.TXCTL,[0x38 | me.TxOrdrs]) # turn on prea/CRC32/EOP
        me.sfrwx (me.sfr.STA1, [0xff]) # clear STA1
        me.sfrwx (me.sfr.FFSTA,[0x00]) # clear FIFO
        me.sfrwx (me.sfr.FFCTL,[0x40]); me.sfrwx (me.sfr.FFIO, me.TxBuffer[:-1]) # first
        me.sfrwx (me.sfr.FFCTL,[0x80]); me.sfrwx (me.sfr.FFIO, me.TxBuffer[-1:]) # last

        sta1 = me.sfrrx (me.sfr.STA1,1)[0]
        if (sta1&0x30)==0x10: # check not discarded
            return TRUE # success
        else:
            return FALSE # discarded


    def msg_tx (me, msgtype, DO=[]):
        '''
        send message and check GoodCRC
        DO is 32-bit
        '''
        me.prltx.msk (0xff, 0x08) # enable auto-RX-GoodCRC
        me.sfrwx (me.sfr.STA0, [0xff]) # clear STA0
        ret = ''
        if me.compose_msg (msgtype, DO): # success
            sta0 = 0
            for xx in range(20): # wait for something rcvd in a period of time
                if sta0 & 0xfc: break;
                sta0 = me.sfrrx (me.sfr.STA0,1)[0]
            if sta0 == 0x00: ret = 'no GoodCRC response, '+ me.OrdrsType[me.TxOrdrs]
            elif (sta0 & 0x40): # GoodCRC rcvd
                me.MyMsgId += 1
                me.MyMsgId &= 7
                # success
            else: # sta0 != 0x0a
                ret = 'bad response, STA0:%02x' % (sta0)
        else:
            ret = 'message discarded'

        me.prltx.pop ()
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

