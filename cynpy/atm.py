
import random
import time

class atm (object):
    '''
    purely a method-only object
    for those SFR master, sfri2c and sfrcsp
    '''

    def sfr_form (me, adr, cnt=16):
        print me.sfrri, adr
        print 'sfr_dump: 0x%02x 0x%02x' % (adr,cnt)
        if ((adr&0x0f)+cnt<=16 and cnt<=8): # in one line
            print '0x%02x:' % adr,
            r_dat = me.sfrri (adr,cnt)
            assert len(r_dat)==cnt, 'sfr read failed'
            for i in range(cnt): print '%02x' % r_dat[i],
        else:
            pos = adr&0x0f
            for ali in range(adr&0xf0,(adr+cnt+15)&0x1f0,0x10):
                print '0x%02x:' % ali,
                r_dat = me.sfrri (ali,16-pos)
                assert len(r_dat)==(16-pos), 'sfr read failed'
                for i in range(0x10):
                    if (i&0x07==0 and i>0): print ' ',
                    if (ali+i<adr or ali+i>=adr+cnt): print '..',
                    else: print '%02x' % r_dat[i-pos],
                print
                pos = 0


    def nvmset (me, ofs):
        assert me.sfrrx (me.sfr.MISC,1)[0] & 0x08, 'MCU is runnung'
        msk = me.sfr.nvmmsk
        me.sfrwx (me.sfr.OFS, [(ofs&msk)&0xff]) # OTP offset [7:0]
        me.sfrwx (me.sfr.DEC, [((ofs&msk)|(0xa000&~msk))>>8]) # OTP offset [??:8], ACK for OTP access


    def nvmrx (me, cnt): # NINC mode
        ret = me.sfrrx (me.sfr.NVMIO, cnt)
        assert len(ret)==cnt, 'NVM read failed'
        return ret


    def nvm_form (me, ofs, cnt):
        assert ofs>=0 and cnt>0 and (ofs+cnt)<=me.sfr.nvmsz, 'out of range'
        print 'remember to halt MCU in advance'
        me.nvmset (ofs)
        if ((ofs&0x0f)+cnt<=16 and cnt<=8): # in one line
            print '0x%04x:' % ofs,
            r_dat = me.nvmrx (cnt)
            for i in range(cnt): print '%02x' % r_dat[i],
            print
        else:
            print 'nvm_form: 0x%04x, %0d' %(ofs,cnt)
            s_pos = ofs&0x0f
            lines = range(ofs&0xfff0,(ofs+cnt+15)&0xfff0,0x10)
            e_pos = 0x0f & (cnt - (16-s_pos))
            for ali in lines:
                print '0x%04x:' % (ali&0x7fff),
                if ali==lines[-1] and e_pos: num = e_pos
                else: num = 16-s_pos
                r_dat = me.nvmrx (num)
                for i in range(0x10):
                    if (i&0x07==0 and i>0): print ' ',
                    if (ali+i<ofs or ali+i>=ofs+cnt): print '..',
                    else: print '%02x' % r_dat[i-s_pos],
                endstr = '  '
                for i in range(0x10):
                    if (ali+i<ofs or ali+i>=ofs+cnt or
                        r_dat[i-s_pos]<ord(' ') or r_dat[i-s_pos]>ord('~')): endstr += '.'
                    else: endstr += chr(r_dat[i-s_pos])
                print endstr
                s_pos = 0
        me.sfrwx (me.sfr.DEC, [(ofs+cnt)>>8]) # clear ACK


    def multi_sfr_write (me, args): # addr=wdat pairs
        assert len(args) > 0, 'addr=wdat pair is a must'
        for it in args[0:]:
            [adr_h, dat_h] = it.split('=')
            print me.sfrwx (int(adr_h,16),[int(dat_h,16)])


    def scope_sfr (me, adr): # read and print the variation
        import KBHit
        kb = KBHit.KBHit ()
        print me.sfrrx
        print 'looped read, press any key.....'
        cnt = 0
        r_min = 0xff
        r_max = 0
        while 1:
            print "\r0x%02x(%0d):" % (adr,cnt),
            try:
                r_dat = me.sfrrx (adr,1)[0]
                if r_dat<r_min: r_min = r_dat
                if r_dat>r_max: r_max = r_dat
                print "%02x %02x %02x" % (r_min,r_dat,r_max),
                cnt += 1
            except:
                print "--",
            if kb.kbhit (): break


    def loopr (me, plist): # looped read and print
        if (len(plist)>0):
            import KBHit
            kb = KBHit.KBHit ()
            print me.sfrrx
            print 'looped read, press any key.....'
            cnt = 0
            while 1:
                print "\r%0d:" % cnt,
                for xx in range (len(plist)):
                    try:
                        r_dat = me.sfrrx (int(plist[xx],16),1)[0]
                        print " %02x: %02x" %(int(plist[xx],16),r_dat),
                        cnt += 1
                    except:
                        print " %02x: --" %(int(plist[xx],16)),
                if kb.kbhit (): break


    def loopw (me, plist): # looped write/read test
        if (len(plist[0])>0):
            import KBHit
            kb = KBHit.KBHit ()
            print me.sfrwx
            print 'looped write/read test, press any key.....'
            cnt = 0
            while 1:
                print "\r%0d:" % cnt,
                for xx in range (len(plist)):
                    wdat = random.randint(0,255)
                    me.sfrwx (int(plist[xx],16), [wdat]);
                    print " %02x: %02x" % (int(plist[xx],16),wdat),
                    r_dat = me.sfrrx (int(plist[xx],16),1)[0]
                    if r_dat!=wdat:
                        print " failed: %02x returned" % (r_dat)
                        exit (-1)
                if kb.kbhit (): break
                cnt += 1


    def preset_adc (me):
        me.sfrwx (me.sfr.DACLSB,[0x06]) # enable DAC1/COMP (DAC_EN=1)
        me.sfrwx (me.sfr.DACCTL,[0x00])
        me.sfrwx (me.sfr.SAREN, [0xff])

    def get_adc8 (me, chn): # multiple channel
        me.preset_adc ()
        me.sfrwx (me.sfr.DACEN, [chn])
        me.sfrwx (me.sfr.DACCTL,[0x0d]) # 8-bit once
        ret = []
        msk = 0x01
        for xx in range(8):
            if chn & (msk<<xx):
                ret += [8 * me.sfrrx (me.sfr.DACV0 + xx, 1)[0]] # mV
        return ret

    def get_adc10 (me, chn): # single channel
        me.preset_adc ()
        if chn==8: # IS channel
            chn = 0
            me.sfrwx (me.sfr.CMPOPT, [0x80]) # COMP_SWITCH=1
            me.sfrwx (me.sfr.CVCTL,  [0x05]) # OCP_EN=1
        else:
            me.sfrwx (me.sfr.CMPOPT, [0x00]) # no switch/swap

        me.sfrwx (me.sfr.DACEN, [0x01 << chn])
        me.sfrwx (me.sfr.DACCTL,[0x4d]) # 10-bit once (not stable)
##        print \
##            2 * (4 * me.sfrrx (me.sfr.DACV0 + chn, 1)[0] \
##                  + (me.sfrrx (me.sfr.DACLSB, 1)[0] & 0x03)),
        me.sfrwx (me.sfr.DACCTL,[0x4f]) # 10-bit loop
        me.sfrwx (me.sfr.DACCTL,[0x00])
        return \
            2 * (4 * me.sfrrx (me.sfr.DACV0 + chn, 1)[0] \
                  + (me.sfrrx (me.sfr.DACLSB, 1)[0] & 0x03))


    def scope_adc (me, chn): # read and print the variation
        import KBHit
        kb = KBHit.KBHit ()
        print 'looped read, press any key.....'
        cnt = 0
        r_max = 0
        r_min = 0xfff
        me.preset_adc ()
        sav0 = me.sfrrx (me.sfr.DACEN, 1)
        me.sfrwx (me.sfr.DACEN, [0x01 << chn])
        me.sfrwx (me.sfr.DACCTL,[0x4F]) # 10-bit looped
        while 1:
            print "\rADC%d(%0d):" % (chn,cnt),
            try:
                r_dat  = me.sfrrx (me.sfr.DACV0 + chn, 1)[0] * 4
                r_dat += me.sfrrx (me.sfr.DACLSB,      1)[0] & 0x03
                if r_dat<r_min: r_min = r_dat
                if r_dat>r_max: r_max = r_dat
                print "%03d %03d %03d mV" % (r_min*2,r_dat*2,r_max*2),
                cnt += 1
            except:
                print "---",
            if kb.kbhit (): break
        me.sfrwx (me.sfr.DACEN, sav0)
        me.sfrwx (me.sfr.DACCTL,[0])


    def pre_prog (me, hiv=0): # provide high voltage
        assert hiv==0 or hiv==1, 'error argument, hiv'
        if me.sfr.name=='CAN1108' or \
           me.sfr.name=='CAN1111':
            rlst = []
            print 'Provide VPP(6.5V) on VC1 for valid programming'
        else:
            if me.sfr.name.find ('CAN1112')==0:
                tmp = me.sfrrx (me.sfr.CCCTL,1)[0]
                if tmp & 0xc0:
                    print 'both Rp is to be turned off'
                    me.sfrwx (me.sfr.CCCTL, [tmp & 0x3f]) # RP?_EN=0

            rlst = \
                me.sfrrx (me.sfr.PWR_V,1) + \
                me.sfrrx (me.sfr.SRCCTL,1) # save PWR_V
            if hiv > 0: # hiv=0 to emulate
                me.sfrwx (me.sfr.PWR_V, [120]) # set VIN=9.6V

            print 'adj-VIN:',
            for xx in range(3):
                print '%5.2f' % (10.0 * me.get_adc10 (0) / 1000),
            print 'V'

            me.sfrwx (me.sfr.SRCCTL, [rlst[1] | 0x40]) # set HVLDO high voltage

            if me.sfr.name.find ('CAN1110')==0:
                me.sfrwx (me.sfr.NVMCTL, [0x10,0x12,0x32]) # set VPP,TM,PROG

        return rlst


    def pst_prog (me, rlst): # resume 5V
        if not \
          (me.sfr.name=='CAN1108' or \
           me.sfr.name=='CAN1111'):
            if me.sfr.name.find ('CAN1110')==0:
                me.sfrwx (me.sfr.NVMCTL, [0x12,0x10,0x00]) # clr PROG,TM,VPP
            me.sfrwx (me.sfr.PWR_V,  [rlst[0]]) # recover VIN
            me.sfrwx (me.sfr.SRCCTL, [rlst[1] &~0x40]) # recover V5 (HVLDO)
#################################################################################
###         discharge on socket board likely causes POR
#           me.sfrwx (me.sfr.SRCCTL, [rlst[1] | 0x02]) # discharge VIN-only
#           me.sfrwx (me.sfr.SRCCTL, [rlst[1] &~0x02])
#################################################################################
###         CC-ISP during voltage decending is not stable
#           print 'pos-VIN:',
#           print '%5.2f' % (10.0 * me.get_adc10 (0) / 1000),
#           for xx in range(3):
#               print '%5.2f' % (10.0 * me.get_adc10 (0) / 1000),
#           print 'V'
#################################################################################
###         so just delay
            time.sleep(1)


    def test (me):
        raise NotImplementedError()


    def nvm_prog (me, adr, wlst, hiv=0): # hiv=0 to emulate
        """
        program @adr those in list 'wlst' byte-by-byte
        slowly write for PROG timing
        """
        me.nvmset (adr)
        rlst = me.pre_prog (hiv)
        for xx in range(len(wlst)):
            me.sfrwx (me.sfr.NVMIO, [wlst[xx]])
        me.pst_prog (rlst)

        dec = me.sfrrx (me.sfr.DEC, 1)[0]
        me.sfrwx (me.sfr.DEC, [(me.sfr.nvmmsk >> 8) & dec]) # clear ACK


    def get_file (me, memfile):
        """
        load file and return the array with byte-by-byte format
        """
        print memfile
        f = 0
        lines = []
        if memfile[-4:].lower() == '.bin':
            f = open(memfile,'rb')
            lines = map(ord,list(f.read()))
        elif memfile[-7:].lower() == '.1.memh' or \
             memfile[-7:].lower() == '.2.memh':
            f = open(memfile,'r')
            for xx in f.readlines():
                text = xx.split()[0] # only the 1st word
                if text != '': # ignore empty
                    assert len(text) == 2 * me.sfr.nbyte, \
                           'invalid format for %s' % (me.sfr.name)
                    if me.sfr.nbyte == 2:
                        lines.append (int(text[2:4],16))
                    lines.append (int(text[0:2],16))

        if f:
            print '%d (0x%04x) byte(s)' % (len(lines),len(lines))
            rem = len(lines) % me.sfr.nbyte
            if rem > 0:
                print 'append 0xFF for programming unit,', me.sfr.nbyte - rem
                for xx in range(me.sfr.nbyte - rem):
                    lines.append (0xff)
            f.close()
        else:
            print 'ERROR: file open'

        return lines


    def nvm_prog_raw_block (me, wrcod):
        me.sfrwx (me.sfr.NVMIO, wrcod)


    def nvm_prog_block (me, addr, wrcod, rawsz, hiv=0, block=256):
        """
        program the in-byte array 'wrcod' into NVM block-by-block
        SFR-by-CSP: limit block size by CSP buffer and dummy
        SFR-by-I2C: 100KHz write for PROG timing
        """
        assert block > 0, 'block size must be positive'
        me.nvmset (addr)
        rlst = me.pre_prog (hiv)
        start = time.time ()

        for xx in range(0, len(wrcod), block):
            wcnt = block if xx+block <= len(wrcod) else len(wrcod)-xx
            me.sfrwx (me.sfr.NVMIO, wrcod[xx:xx+wcnt])

        me.pst_prog (rlst)
        print "%.1f sec" % (time.time () - start)

        dec = me.sfrrx (me.sfr.DEC, 1)[0]
        me.sfrwx (me.sfr.DEC, [(me.sfr.nvmmsk >> 8) & dec]) # clear ACK

        ofs = me.sfrrx (me.sfr.OFS, 1)[0]
        endadr = (ofs+dec*256) & me.sfr.nvmmsk
        print ('ERROR: 0x%04x' % (endadr)) \
        if endadr != (addr + rawsz) & me.sfr.nvmmsk else 'complete'


    def nvm_upload_block (me, memfile, hiv=0):
        """
        load the memory file 'memfile' for uploading to NVM
        """
        print 'program NVM...',
        wrcod = me.get_file (memfile)
        me.nvm_prog_block (0, wrcod, len(wrcod), hiv)


    def show_mismatch (me, adr, dat, exp, num, limit=50):
        """
        for counting number of mismatch
        and show mismatch messages
        """
        if dat != exp:
            if num  < limit:   print '0x%04X : %02X %c (!=%02X)' % (adr, dat, chr(dat) if chr(dat)>' ' and dat<128 else ' ', exp)
            if num == limit:   print 'further mismatch is suppressed',
            if num == limit+1: print '\rfurther mismatches are suppressed',
            return 1
        else:
            return 0


    def nvm_chk_blank (me, start, end, mismatch, block=256): # the byte 'end' is not compared
        """
        check if those contents are all '1' block-by-block
        """
        print 'blank check from 0x%04x to 0x%04x' % (start, end),
        me.nvmset (start)
        while start < end:
            rcnt = block if start+block <= end else end-start
            rdat = me.nvmrx (rcnt)
            for yy in range(len(rdat)):
                mismatch += me.show_mismatch (start+yy, rdat[yy], 0xff, mismatch)
            start += rcnt

        me.sfrwx (me.sfr.DEC, [end>>8]) # clear ACK
        return mismatch


    def nvm_comp_block (me, expcod, block=256, blank_check=0):
        print 'block size =', block
        mismatch = 0
        me.nvmset (0)
        start = time.time ()
        for xx in range(0,len(expcod),block):
            rcnt = block if xx+block <= len(expcod) else len(expcod)-xx
            rdat = me.nvmrx (rcnt)
            for yy in range(len(rdat)):
                mismatch += me.show_mismatch (yy+xx, rdat[yy], expcod[yy+xx], mismatch)

        if blank_check:
            if mismatch: print
            mismatch = me.nvm_chk_blank (xx + rcnt, me.sfr.nvmsz, mismatch, block)

        print '%.1f sec' % (time.time () - start)
        dec = me.sfrrx (me.sfr.DEC, 1)[0]
        me.sfrwx (me.sfr.DEC, [(me.sfr.nvmmsk >> 8) & dec]) # clear ACK

        print ('mismatch: %s' % (mismatch)) if mismatch else 'complete'


    def nvm_compare (me, cmdparam):
        '''
        general purpose comparison procedure
        parse the command line
        '''
        blank_check = 0
        block_num = -1
        print 'compare NVM content...',
        expcod = me.get_file (cmdparam[0]) # memfile
        if len(cmdparam) > 1: # exception(s)
            for it in cmdparam[1:]:
                if it == 'blank': # do blank check
                    blank_check = 1
                else:
                    [adr_h, text] = it.split('=')
                    if adr_h == 'block':
                        block_num = int(text,10)
                    else:
                        adr = int(adr_h,16)
                        if text[0]=='\\':
                            expcod[adr] = int(text[1:],16)
                        else:
                            for tt in range(len(text)):
                                if adr+tt < len(expcod):
                                    expcod[adr+tt] = ord(text[tt])

        if block_num > 0: me.nvm_comp_block (expcod, block_num, blank_check)
        else:             me.nvm_comp_block (expcod, blank_check=blank_check)


    def nvm_download (me, binfile):
        '''
        download NVM from the target (TST slave)
        save into the binary file 'binfile'
        detect upper boundary for ending the file
        '''
        print 'download NVM...', binfile
        dncode = ''
        lastcode = 0
        block = 34
        start = time.time ()
        me.nvmset (0)
        for xx in range(0, me.sfr.nvmsz, block):
            rcnt = block if xx+block <= me.sfr.nvmsz else me.sfr.nvmsz - xx
            rdat = me.nvmrx (rcnt)
            dncode += ''.join(chr(e) for e in rdat)
            for yy in range(rcnt):
                if rdat[yy] != 0xff:
                    lastcode = xx + yy

        print '%.1f sec' % (time.time () - start)
        dec = me.sfrrx (me.sfr.DEC, 1)[0]
        me.sfrwx (me.sfr.DEC, [(me.sfr.nvmmsk >> 8) & dec]) # clear ACK

        print len(dncode), 'bytes read'
        print lastcode+1, '(0x%04x) bytes written' % (lastcode+1)

        f = open(binfile,'wb')
        if f:
            f.write(dncode)
            f.close()
        else:
            print 'ERROR: file open'


    def get_trim (me):
        '''
        search the trim MTTable
        get the newest entry
        '''
        me.nvmset (me.sfr.trimtable)
        ret = [] # empty if not found
        rdat = me.nvmrx (me.sfr.trimsz *me.sfr.trimnum)
        for xx in range(me.sfr.trimnum):
            cnt_not_ff = 0
            for yy in range(me.sfr.trimsz):
                if rdat[xx*me.sfr.trimsz + yy] != 0xff:
                    cnt_not_ff += 1
            if cnt_not_ff == 0 and xx > 0: # found
                ret = rdat[(xx-1)*me.sfr.trimsz : xx*me.sfr.trimsz]
                break

        dec = me.sfrrx (me.sfr.DEC, 1)[0]
        me.sfrwx (me.sfr.DEC, [(me.sfr.nvmmsk >> 8) & dec]) # clear ACK
        return ret


    def set_trim (me):
        '''
        '''
        trimvec = me.get_trim ()
        print ['0x%02x' % xx for xx in trimvec]
        print me.sfrwi (me.sfr.trimsfr, trimvec)


    def shift_osc (me, delta):
        '''
        signed int 'delta' for slower/faster OSC
        '''
        org = me.sfrrx (me.sfr.sfr_osc, 1)[0]
        new = me.sfr.get_osc (org, delta)
        me.sfrwx (me.sfr.sfr_osc, [new])
        print 'OSC trim [0x%02X]: 0x%02X -> 0x%02X' % (me.sfr.sfr_osc, org, new)
