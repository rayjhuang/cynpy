
from updprl import *

class ams (updprl):
    '''
    Atomic Message Sequence
    1. auto-responding
    2. initiator
    Note:
    a. enable auto-TX/RX-GoodCRC during TX/RX
    b. via AARDVARK (USB-I2C bridge) on virtual machine doesn't work
    '''

    def __init__ (me, i2cmst, deva, check_kb_func, sleep_func, ordrs=0):
        '''
        initial as a PD3 SINK with VCONN sink
        '''
        super(ams,me).__init__ (i2cmst, deva, ordrs)
        me.check_kb_func = check_kb_func
        me.sleep_func = sleep_func

        me.RcvdPdo = []
        me.PosMinus = 0 # save the prior issued RDO position

        me.str = '' # command string
        me.kb = ord('1') # command from keyboard
        me.mode = 0 # 0/1/2/3 : RX-TX/RX-PPS/TX/PPS
        me.MaxCurrent = 0 # specified max current
        me.OprCurrent = 0 # specified operating current
        me.TargetVolt = 0 # specified target voltage in PPS
        me.AttentionCmd= 0x10 # specified command in sending Attention (checksum)
        me.ppstime = 0
        me.SpecRev = 2 # PD_R3


    def upd_tx (me, cmd, do=[]):
        me.sfrwx (me.sfr.STA0, [0xff]) # clear STA0, prepare for the 1st 'quick' upd_rx
        me.sfrwx (me.sfr.STA1, [0xff]) # clear STA1
        me.msg_tx (cmd, do)

        msg = 'TX - %02X%02X' % (me.TxBuffer[1],me.TxBuffer[0]) \
                                          + (':' if len(do) > 0 else '')
        for yy in range(len(do)): # NDO
            msg += ' %08X' % do[yy]
        print '%s (%s)' % (msg, me.DataMsg[cmd] if len(do) > 0 else me.CtrlMsg[cmd])


    def ams_request (me):
        '''
        '''
        rdo = (me.PosMinus+1) << 28
        ret = (FALSE,FALSE) # not a APDO, not accepted
        tar = 0
        mxc = 0
        if len(me.RcvdPdo) > me.PosMinus:
            if (me.RcvdPdo[me.PosMinus] >> 30) == 3: # APDO
#               ppsmax = ((me.RcvdPdo[me.PosMinus] >> 17) & 0x7f) # 100mV
#               ppsmin = ((me.RcvdPdo[me.PosMinus] >> 8)  & 0x7f) # 100mV
                ret = (TRUE,ret[1]) # request to a APDO
                if me.ppstime >= 0: # no matter accepted or not
                    me.ppstime = 0
                if me.TargetVolt == 0:
                    me.TargetVolt = ((me.RcvdPdo[me.PosMinus] >> 17) & 0x7f) * 100
                tar =  (me.TargetVolt / 20) & 0x7ff
                opc = ((me.OprCurrent / 50) if me.OprCurrent > 0 else me.RcvdPdo[me.PosMinus]) & 0x7f
            else:
                opc = ((me.OprCurrent / 10) if me.OprCurrent > 0 else me.RcvdPdo[me.PosMinus]) & 0x3ff
                mxc = ((me.MaxCurrent / 10) if me.MaxCurrent > 0 else me.RcvdPdo[me.PosMinus]) & 0x3ff
        else:
            print 'not yet PDO received, all fixed PDO assumed'
            opc = (me.OprCurrent / 10) & 0x3ff
            mxc = (me.MaxCurrent / 10) & 0x3ff

        rdo |= opc | (mxc << 10) | (tar << 9)

        me.upd_tx (2, [rdo]) # Request
        (ndo,mtyp,do) = me.upd_rx (quick=1)
        if (ndo,mtyp) == (0,3): # Accept
            ret = (ret[0],TRUE) # accepted
            me.upd_rx () # PS_RDY

        if   me.mode == 2 and ret == (TRUE,TRUE): # APDO accepted
            me.mode = 3
            print '[AMS_PPS]'
        elif me.mode == 3 and ret == (FALSE,TRUE): # non-APDO accepted
            me.mode = 2
            print '[AMS_TX]'


    def ams_get_source_cap (me):
        '''
        '''
        me.upd_tx (7) # Get_Source_Cap
        (ndo,mtyp,do) = me.upd_rx (quick=1)
        if ndo > 0 and mtyp == 1: # SourceCap
            me.RcvdPdo = do
            me.ams_request ()


    def ams_dr_swap (me):
        me.upd_tx (9) # DR_Swap
        (ndo,mtyp,do) = me.upd_rx (quick=1)
        if ndo == 0 and mtyp == 3: # Accept
            me.DataRole = 1 - me.DataRole # swap


    def ams_vconn_swap (me):
        me.upd_tx (11) # VCONN_Swap
        (ndo,mtyp,do) = me.upd_rx (quick=1)
        if ndo == 0 and mtyp == 3: # Accept
            if me.Vconn: # VCONN source to become sink
                me.upd_rx () # PS_RDY (10ms, too soon to get this!!!!!!!!!!!!)
            else:
                me.upd_tx (6) # PS_RDY to become source

            me.Vconn = 1 - me.Vconn # swap


    def ams_attention (me):
        if (me.AttentionCmd&0xff) == 0x10: # checksum
            me.upd_tx (15,[0x2a418006,me.AttentionCmd]) # SVDM (Attention)
            (ndo,mtyp,do) = me.upd_rx (quick=1)
            me.upd_tx (15,[0x2a410010]) # UVDM
        elif (me.AttentionCmd&0xff) == 0x02: # program
            me.upd_tx (15,[0x2a418006,me.AttentionCmd]) # SVDM (Attention)
            print 'MCU stopped, DATEX table', (me.AttentionCmd>>8)&0x3, \
                  'is ready for programming'
        else:
            print 'Attention command ', me.AttentionCmd, ' not supported'
            

    def ams_goto_rx (me, cmd=0):
        '''
        cmd=1 : Send a Hard Reset ordered set
        goto AMS_RX
        '''
        if cmd == 1: me.ordered_set (1) # Hard Reset
        me.mode = 0 if me.mode==2 else 1
        print '[AMS_RX]'


    def pps_timer (me):
        '''
        '''
        if me.ppstime >= 0:
            me.ppstime += 1
        me.sleep_func (0.01)
        if me.ppstime == 966: # about 10 sec
            me.ams_request () # reset me.ppstime in this


    def ams_tx (me):
        '''
        '''
        if   me.kb == ord('q'): me.ams_goto_rx () # 'q'
        elif me.kb == ord('r'): me.ams_goto_rx (1) # Hard Reset
        elif me.kb == ord('g'): me.ams_get_source_cap () # Get_Source_Cap
        elif me.kb == ord('d'): me.ams_dr_swap () # DR_Swap
        elif me.kb == ord('v'): me.ams_vconn_swap () # VCONN_Swap
        elif me.kb == ord('a'): me.ams_attention () # Attention

        elif me.kb >= ord('1') and me.kb <= ord('7'): # Request
            me.PosMinus = (me.kb - ord('1')) & 0x07
            me.ams_request ()

        elif me.mode == 2: # additional command only in AMS_TX
            pass

        elif me.mode == 3: # additional command only in AMS_PPS
            if me.kb == ord('+') : me.TargetVolt += 20
            if me.kb == ord('-') : me.TargetVolt -= 20

            if   me.kb == ord('+') or \
                 me.kb == ord('-') or \
                 me.kb == ord('*'): # inc/dec/same
                me.ams_request ()

            elif me.kb == ord('/'): # switch SinkPPSPeriodTimer
                me.ppstime = 0 if me.ppstime < 0 else -1
                print 'switch SinkPPSPeriodTimer', 'ON' if me.ppstime == 0 else 'OFF'


    def ams_rx (me):
        '''
        get/decode a RX message, respond if needed
        '''
        (ndo,mtyp,do) = me.upd_rx () # sunk
        if ndo > 0: # data message
            if mtyp == 1: # SourceCap
                me.RcvdPdo = do # save the received PDO(s)
                me.ams_request ()
                
        elif ndo == 0: # control message
            if mtyp < 0: # Hard/Cable Reset
                print 'RX -', me.OrdrsType[mtyp+7]

        else: # 'q' pressed
            me.mode = 2 if me.mode == 0 else 3
            print '[AMS_TX]' if me.mode == 2 else '[AMS_PPS]'


    def upd_rx (me, quick=0):
        '''
        wait for an auto-TX-GoodCRC sent, then,
        get STA0, get FFSTA, get RX data all take time
        if another RX arrive during these, those data is corrupted
        quick=1 to not clear STA* for a new message may have arrived
            (TX caller is responsible for clearing the STA*)
        '''
        me.prltx.msk (0xff, 0x80) # enable auto-TX-GoodCRC
        if quick == 0:
            me.sfrwx (me.sfr.STA0, [0xff]) # clear STA0
            me.sfrwx (me.sfr.STA1, [0xff]) # clear STA1
        (sta0,sta1) = (0,0)
        (ndo,mtyp,do,key) = (0,0,[],0)
        msg = ''
        while not (sta1 & 0x40) and \
              not (sta0 & 0x80):
            sta0 = me.sfrrx (me.sfr.STA0,1)[0]
            sta1 = me.sfrrx (me.sfr.STA1,1)[0]
            me.kb = me.check_kb_func ()
            if me.kb >= ord('1') and me.kb <= ord('7'):
                me.PosMinus = (me.kb - ord('1')) & 0x07
                print 'PDO'+chr(me.kb), 'is to be requested' # this 'kb' will effect the next Nego
            elif me.kb == ord('q'):
                ndo = -1
                break

            elif me.kb == ord('h'):
                me.help ()

        if ndo == 0: # not break

            if sta1 & 0x40: # auto-TX-GoodCRC sent
                ffcnt = me.sfrrx (me.sfr.FFSTA,1)[0] & 0x3f
                assert ffcnt > 0, 'empty FIFO received'

                me.sfrwx (me.sfr.FFCTL, [0x40]) # first
                rdat = me.sfrrx (me.sfr.FFIO, ffcnt)
                assert ffcnt == len(rdat), 'FIFO read error'

                ndo = (rdat[1] >> 4) & 0x07
                mtyp = rdat[0] & 0x1f
                do = [0] * ndo
                msg = 'RX - %02X%02X' % (rdat[1],rdat[0]) + (':' if ndo > 0 else '')
                for yy in range(ndo):
                    for xx in range(4):
                        do[yy] += rdat[yy*4+2+xx]*(256**xx)
                    msg += ' %08X' % do[yy]
                print msg

            else: # Hard/Cable Reset rcvd
                prls = me.sfrrx (me.sfr.PRLS,1)[0] & 0x70
                if   prls == 0x60: mtyp = -2 # Hard Reset
                elif prls == 0x70: mtyp = -1 # Cable Reset
                else:
                    raise NameError('not recognized ordered set')

#       print msg, quick, ndo, '%02x %02x' % (sta0,sta1)
        me.prltx.pop () # recover PRLTX settings
        return (ndo,mtyp,do)


    def main_loop (me):
        '''
        '''
        if me.mode <= 1: me.ams_rx () # sunk
        if me.mode == 3: me.pps_timer ()
        me.kb = me.check_kb_func ()

        if me.str == '': # 1-key mode

            me.ams_tx ()
            
            if   me.kb == ord(' '): # toogle PD2/3
                me.SpecRev = 3 - me.SpecRev
                print '[PD%d0]' % (me.SpecRev + 1)

            elif me.kb == ord('h'):
                me.help ()

            elif me.kb == ord('>') or \
                 me.kb == ord('=') or \
                 me.kb == ord('<') or \
                 me.kb == ord('?'): # go string specifying mode
                me.str = chr(me.kb)
                print me.str, '\x0D',

        else: # string specifying mode
            if me.kb == 13: # press 'enter' to exec 'me.str'
                if me.str[0] == '>': # specify operating current
                    opc = me.str.split('>')[-1]
                    if opc.isdigit():
                        me.OprCurrent = int(opc)
                        me.str += 'mA op. current'
                if me.str[0] == '<': # specify max. current
                    mxc = me.str.split('<')[-1]
                    if mxc.isdigit():
                        me.MaxCurrent = int(mxc)
                        me.str += 'mA max. current'
                if me.str[0] == '=': # specify target voltage
                    tar = me.str.split('=')[-1]
                    if tar.isdigit():
                        me.TargetVolt = int(tar)
                        me.str += 'mV target voltage'
                if me.str[0] == '?': # specify Attention command
                    tar = me.str.split('?')[-1]
                    if tar.isdigit():
                        me.AttentionCmd = int(tar)
                        me.str += ' Attention command specified'
                print me.str
                me.str = '' # reset 'me.str'
            elif me.kb > ord(' '):
                me.str += chr(me.kb)
                print me.str, '\x0D',

        return me.kb


    def help (me):
        print '''\
        \rInstructions.....
        \r----------------------------------
        \rMODE  [AMS_RX]
        \r    '1'-'7' : PDO position for request
        \r    'q'     : go AMS_TX
        \r    'h'     : show this message
        \rMODE  [AMS_TX]
        \r    'g'     : send Get_Source_Cap and nego. again
        \rMODE  [AMS_PPS]
        \r    '+'     : request again with increased target voltage
        \r    '-'     : request again with decreased target voltage
        \r    '*'     : request again with same target voltage
        \r    '/'     : turn on/off SinkPPSPeriodTimer
        \r----------------------------------
        \rin [AMS_TX] or [AMS_PPS]
        \r(1-key command)
        \r    '1'-'7' : request the PDO
        \r    'a'     : SVDM (Attention)
        \r    'v'     : VCONN_Swap
        \r    'd'     : DR_Swap
        \r    'r'     : Hard Reset
        \r    'q'     : go AMS_RX
        \r    |ESC|   : exit
        \r    |SPACE| : switch PD2/PD3
        \r    'h'     : show this message
        \r(specifying command, ended by |RETURN|)
        \r    '?'     : Attention command
        \r              2/258/514/770 : program
        \r              10 : checksum
        \r    '='     : target voltage (PPS)
        \r    '>'     : operating current (fixed/PPS)
        \r    '<'     : max. current (fixed)
        '''
