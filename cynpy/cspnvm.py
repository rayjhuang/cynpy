
import sys, time

class cspnvm (object):
    '''
    purely a method-only object
    for CSP SFR master, sfrcsp
    '''

    def nvm_burst_initial (me):
        ''' initialize the bridge
            show its FW information
            set I2C non-INC mode
            initial PG0
        '''
        me.busmst.sfrwx (me.busmst.sfr.MISC,  [0x08]) # hold MCU
        me.busmst.sfrwx (me.busmst.sfr.I2CCTL,[0x10 | me.busmst.sfr.inc]) # PG0 writable, NINC
        me.busmst.sfrwx (me.busmst.sfr.DEC,   [0xa9])
        me.busmst.sfrwx (me.busmst.sfr.OFS,   [0])
        for yy in range(4): # show OTP header
            for xx in me.busmst.sfrrx (me.busmst.sfr.NVMIO,16):
                sys.stdout.write ('%c' % xx)
            print

        me.busmst.sfrwx (me.busmst.sfr.DEC,   [0])
#       me.busmst.sfrwx (me.busmst.sfr.MISC,  [0x02]) # tell bridge to plus 1 dummy
        me.busmst.sfrwx (me.busmst.sfr.RXCTL, [0x01 >> me.busmst.TxOrdrs])
        me.busmst.sfrwx (me.busmst.sfr.TXCTL, [0x38 | me.busmst.TxOrdrs]) # SOP"_Debug
        me.busmst.sfrwx (me.busmst.sfr.SRST,  [1,1,1]) # reset MCU of bridge


    def nvm_burst_next_pg0 (me, pg0):
        ''' set/change PG0 with I2C INC mode
            poll and wait for R.ACK=1
        '''
        sys.stdout.write ('.')
        me.busmst.sfrwx (me.busmst.sfr.I2CCTL, \
                         [0x10 | pg0<<1 | ~me.busmst.sfr.inc]) # PG0 writable, INC
        rsp = 0
        for xx in range(1000): # wait for a limited period
            rsp = me.busmst.sfrrx (0,1)[0] # loop if R.ACK=0
            if rsp != 0: # something happened
                break
        if rsp != 1:
            print 'WRITER_ERROR: %d, %x' % (xx, rsp)
        return rsp


    def nvm_upload_burst (me, memfile, hiv=0):
        wrcod = me.get_file (memfile)
        assert len(wrcod) > 0, 'file size must be positive'
        me.nvm_burst_initial ()
        me.nvmset (0)
        rlst = me.pre_prog (hiv)
        start = time.time ()

        block = 125 # 128 - SENDING_STA - RESPONSE_STA - INFO
        cmd = 1 # initiate a burst
        for xx in range(0, len(wrcod), block):
            if me.nvm_burst_next_pg0 (pg0) != 1:
                break
            me.busmst.sfrwx (0, [0,block] + wrcod[xx:xx+block] + [cmd]) # PG0 INC write
            cmd = 2 # continue the burst
            pg0 = 1 - pg0

        print 'FFSTA:0x%02x' % me.busmst.sfrrx (me.busmst.sfr.FFSTA,1)[0]
        for xx in range(1000):
            if (me.busmst.sfrrx (me.busmst.sfr.STA1,1)[0] & 0x01):
                print 'polling:', xx
                break

        print "%.1f sec" % (time.time () - start)
        me.pst_prog_1110 (rlst)
        ofs = me.sfrrx (me.sfr.OFS, 1)[0]
        dec = me.sfrrx (me.sfr.DEC, 1)[0]
        endadr = (ofs+dec*256) & me.sfr.nvmmsk
        me.sfrwx (me.sfr.DEC, [endadr>>8]) # clear ACK

        print ('ERROR: 0x%04x' % (endadr)) if endadr != len(wrcod) else 'complete'
