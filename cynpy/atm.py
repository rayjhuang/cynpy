
import random
import time

from nvm import nvm

class atm (nvm):
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


    def scope_sfr (me, adr, n_avg=1): # read and print the variation
        assert n_avg > 0, 'avg number is at least 1'
        import KBHit
        kb = KBHit.KBHit ()
        print me.sfrrx
        print 'looped read (avg=%d), press any key.....' % n_avg
        cnt = 0
        r_avg = [0] * n_avg
        while 1:
            print "\r0x%02x(%03d):" % (adr,cnt),
            try:
                r_dat = me.sfrrx (adr,1)[0]
                r_avg.pop()
                r_avg.insert(0,r_dat)
#               r_cnt = [0] * 256
                r_sum = 0
                r_min = 0xff
                r_max = 0
                for i in range(n_avg):
                    r_sum += r_avg[i]
                    if r_dat<r_min: r_min = r_dat
                    if r_dat>r_max: r_max = r_dat
#                   r_cnt[r_avg[i]] += 1
#               print r_avg,
#               print "%02x %02x %02x" % (r_min,r_sum/n_avg,r_max),
                print "%3d %3d %3d" % (r_min,r_sum/n_avg,r_max),
                cnt += 1
            except:
                print "--",
            if kb.kbhit (): break


    def multi_write (me, args, verbose=1): # addr=wdat pairs
        assert len(args) > 0, 'addr=wdat pair is a must'
        for it in args[0:]:
            [adr_h, dat_h] = it.split('=')
            rs = me.sfrwx (int(adr_h,16),[int(dat_h,16)])
            if verbose: print rs


    def loop_write (me, plist): # looped writing
        if (len(plist)>0):
            import KBHit
            kb = KBHit.KBHit ()
            print me.sfrwx
            print 'looped writing, press any key.....'
            cnt = 1
            while 1:
                print "\r%0d" % cnt,
                me.multi_write (plist,0)
                if kb.kbhit (): break
                cnt += 1

      
    def loop_read (me, plist): # looped read and print
        if (len(plist)>0):
            import KBHit
            kb = KBHit.KBHit ()
            print me.sfrrx
            print 'looped read, press any key.....'
            cnt = 1
            while 1:
                print "\r%0d:" % cnt,
                for xx in range (len(plist)):
                    try:
                        r_dat = me.sfrrx (int(plist[xx],16),1)[0]
#                       print " %02x: %02x" %(int(plist[xx],16),r_dat),
                        print " %02x: %3d" %(int(plist[xx],16),r_dat),
                    except:
                        print " %02x: --" %(int(plist[xx],16)),
#               if not (cnt%10): print
                if kb.kbhit (): break
                cnt += 1


    def loop_w_r (me, plist): # looped write/read test
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


    def test (me, wlst):
        raise NotImplementedError()


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
            rcnt = block if xx+block < me.sfr.nvmsz else me.sfr.nvmsz - xx
            rdat = me.nvmrx (rcnt)
            dncode += ''.join(chr(e) for e in rdat)
            for yy in range(rcnt):
                if rdat[yy] != 0xff:
                    lastcode = xx + yy

        print '%.1f sec' % (time.time () - start)
        dec = me.sfrrx (me.sfr.DEC, 1)[0]
        me.sfrwx (me.sfr.DEC, [(me.sfr.nvmmsk >> 8) & dec]) # clear ACK

        print len(dncode), '(0x%04x) bytes read' % len(dncode)
        print lastcode+1, '(0x%04x) bytes written' % (lastcode+1)

        f = open(binfile,'wb')
        if f:
            f.write(dncode)
            f.close()
        else:
            print 'ERROR: file open'


    def get_trim (me):
        '''
        search the trim table (a MTP table)
        get the newest entry
        '''
        me.nvmset (me.sfr.trimtable['addr'])
        rdat = []
        for ii in range(me.sfr.trimtable['width']):
            rdat += me.nvmrx (me.sfr.trimtable['depth'])

        ret = [] # empty if not found
        for xx in range(me.sfr.trimtable['depth']):
            cnt_not_ff = 0
            for yy in range(me.sfr.trimtable['width']):
                if rdat[xx*me.sfr.trimtable['width'] + yy] != 0xff:
                    cnt_not_ff += 1
            if cnt_not_ff == 0 and xx > 0: # found
                ret = rdat[(xx-1)*me.sfr.trimtable['width'] \
                             : xx*me.sfr.trimtable['width']]
                break

        dec = me.sfrrx (me.sfr.DEC, 1)[0]
        me.sfrwx (me.sfr.DEC, [(me.sfr.nvmmsk >> 8) & dec]) # clear ACK
        return ret


    def set_trim (me):
        '''
        '''
        trimvec = me.get_trim ()
        print ['%02x' % xx for xx in trimvec]
        for ii in range(len(me.sfr.trimsfr)):
            print me.sfrwx (me.sfr.trimsfr[ii],[trimvec[ii]])


    def shift_osc (me, delta):
        '''
        signed int 'delta' for slower/faster OSC
        '''
        org = me.sfrrx (me.sfr.sfr_osc, 1)[0]
        new = me.sfr.get_osc (org, delta)
        assert new<=127 and new >=-128, ('SFR(OSC) to be out-of-range', new)
        me.sfrwx (me.sfr.sfr_osc, [new])
        print 'OSC trim [0x%02X]: 0x%02X -> 0x%02X' % (me.sfr.sfr_osc, org, new)

