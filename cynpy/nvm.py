
import time

class nvm (object):
    '''
    purely a method-only object
    for atm's prog/comp testing
    '''

    def parse_backslash (me, it):
        """
        \_ : ascii/hex string
        """
        rtn = []
        if it[0]=='\\': # start an ascii string (LSB at head)
            rtn = map(ord,list(it[1:]))
        else: # a hex string (LSB at tail)
            it = it.replace('_','') # ignore '_'
            it = '0'+it if (len(it))%2 else it # let len even
            for tt in range(len(it)/2,0,-1):
                rtn += [int(it[tt*2-2:tt*2],16)]
        return rtn

    def parse_asterisk (me, it):
        """
        *  : a string can be multi
        """
        rtn = []
        if it.find ('*') < 0: # '*' not found
            rtn = me.parse_backslash (it)
        else:
            [left,right] = it.split('*')
            rtn = me.parse_backslash (left) * int(right)
        return rtn

    def parse_argvlst (me, argvlst):
        """
        command line data list
        =  : option assignment
             addressed assignment '@' if 'file' is assigned
        """
        data_list = []
        addr_assign = [] # ordered assignment
        assert len(argvlst)>=2, 'start address not found'
        rtn = {'data' : data_list, \
               'addr' : addr_assign, \
               'start': int(argvlst[1],16)}
        for it in argvlst[2:]: # argv[0] is nvm(cmd), argv[1] is start_addr
            if it.find ('=') < 0: # '=' not found
                if len(addr_assign):
                    addr_assign[-1] += me.parse_asterisk (it)
                else:
                    data_list += me.parse_asterisk (it)
            else:
                [left,right] = it.split('=')
                if left[0]=='@': # addressed assignment
                    addr_assign += [[left[1:]] + me.parse_asterisk (right)]
                else: # option assignment
                    assert not left in rtn, "invalid '%s='" % left
                    rtn[left] = right
        return rtn

    def get_data_list (me, argvlst):
        """
        expcod base is defined by either
          1. addr+file
          2. addr+(sequential data list)
          exceptions from command line (addressed assignment) to modify the base
          priority: tail > head > file
        """
        param = me.parse_argvlst (argvlst)
        if 'file' in param:
            assert len(param['data'])==0, 'either file= or data_list'
            param['data'] = me.get_file (param['file'])
#       else:
#           assert len(param['data'])>0, 'no data_list to do'

        if 'end' in param: # higher priority
            param['end'] = int(param['end'],16)
        else:
            param['end'] = param['start'] + len(param['data'])

        for assign in param['addr']:
            for ii in range(len(assign[1:])):
                addr = ii + int(assign[0],16)
                if addr < param['end']:
                    param['data'][addr-param['start']] = assign[ii+1]
                else:
                    print 'out-range assign'

        if 'block' in param:
            assert not 'blockw' in param and \
                   not 'blockr' in param, "invalid 'block='"
            param['blockw'] = param['block']
            param['blockr'] = param['block']
        return param


    def nvmcomp (me, param):
        """
        blank= : blank check no/both/front/rear
        """
        if not 'no_note' in param:
            print 'check from 0x%04x to 0x%04x' % (param['start'],param['end']-1),
        start = time.time ()
        mismatch = 0
        if not 'blockr' in param or param['blockr']=='':
            mismatch = me.nvm_block_chk (param['start'], param['data'])
        else:
            block = int(param['blockr'])
            assert block>0, "invalid 'blockr', %d" % block
            mismatch = me.nvm_block_chk (param['start'], param['data'], block)

        if not 'no_note' in param:
            print ('\nmismatch: %s' % (mismatch)) if mismatch else 'complete'
            print '%.1f sec' % (time.time () - start)


    def nvmprog (me, param):
        """
        hiv=0 to emulate (won't switch VPP) and check
        hiv=1 to byte-programming
        hiv=2 to byte-programming and check
        """
        note = False if 'no_note' in param else True
        print 'program from 0x%04x to 0x%04x' % (param['start'],param['end']-1),
        hiv = 0 if not 'hiv' in param else int(param['hiv'])
        assert hiv>=0 and hiv<=2, "invalid 'hiv', %d" % hiv
        if not 'blockw' in param or param['blockw']=='':
            me.nvm_prog_block (param['start'], param['data'], len(param['data']), hiv=hiv>0, note=note)
        else:
            block = int(param['blockw'])
            assert block>0, "invalid 'blockw', %d" % block
            me.nvm_prog_block (param['start'], param['data'], len(param['data']), block, hiv>0, note=note)

        if hiv==0 or hiv==2:
            me.nvmcomp (param)


    def nvmsegm (me, param): # segmented prog/comp
        """
        segm=
        intr=
        wait=
        """
#       me.recognize (param, ['segm','wait'])
        temp = param.copy()
        temp['no_note'] = ''
        segm = int(param['segm']) if 'segm' in param else 64
        intr = int(param['intr']) if 'intr' in param else 0 # number of segment
        wait = float(param['wait']) if 'wait' in param else 0
        num = len(param['data']) / segm + (1 if \
              len(param['data']) % segm else 0) # total segment number

        ptr = 0 # select a segment to do
        for ii in range(num):
            if wait and ii:
                print 'wait %.1f sec(s)' % wait
                time.sleep (wait) # wait for NVM (ATTOP) cooldown

            temp['data'] = []
            addr = param['start'] + (ptr*segm)
            for xx in range(segm):
                if addr+xx < param['end']:
                    temp['data'] += [param['data'][ptr*segm+xx]]

            temp['start'] = addr
            temp['end'] = addr + len(temp['data'])
            print 'SEGM: %3d, %3d ---' % (ptr, len(temp['data'])),
            me.nvmprog (temp)

            if wait==0: print
            ptr = ptr+(1+intr) if ptr+(1+intr) < num \
                       else (ptr+1) % (1+intr) # wrap around


    def nvmintr (me, param): # interleaved prog/comp
        """
        segm=
        intr=
        """
        temp = param.copy()
        temp['no_note'] = ''
        segm = int(param['segm']) if 'segm' in param else 64
        intr = int(param['intr']) if 'intr' in param else 0x2000
        for ii in range(param['start'],param['end'],segm):
            print 'SEGM: %3d ---' % ((ii-param['start'])/segm),
            temp['data'] = []
            for xx in range(segm):
                if ii+xx < param['end']:
                    temp['data'] += [param['data'][ii+xx-param['start']]]
            num = (ii / segm) % (0x4000 / intr) # in range of 0x4000
            temp['start'] = (ii + num*intr) % 0x4000
            temp['end'] = temp['start'] + len(temp['data'])
            me.nvmprog (temp)
            print


    def nvmsum15 (me, param):
        """
        start: start address (even number)
        end  : count (word)
        check empty IC w/ TCODE:
        X:\project\git\workpy\cynpy>python -B csp.py nvmsum15 0 end=900 no_note=
        """
        assert param['start'] < param['end'], 'invalid end address'
        (hi,lo,sum) = (0,0,0)
        print 'summation from 0x%04x to 0x%04x' % (param['start'],param['end']-1)
        if 'file' in param:
            rdat = param['data'][param['start']:]
            if 'tcode' in param:
                sum = -(~(int(param['tcode'],16)+0x7f00))
                print 'summation with TCODE_%02X' % (int(param['tcode'],16)) # CAN1123A0: FB
        else:
            rdat = me.nvm_block_read (param['start'],param['end']-param['start'])

        for ii in range(param['end']-param['start']): # count (byte)
            if (param['start']+ii)%2:
                hi = (~rdat[ii])%256
                sum += lo + (hi*256 if hi<0x80 else (hi-0x80)*256 + 1)
                sum %= 256*128
                if not 'no_note' in param:
                    print '0x%04x:' % (param['start']+ii-1),
                    print '%02x %02x => %02x %02x =>' % (rdat[ii],rdat[ii-1],lo,hi),
                    print '0x%04x (%d)' % (sum,sum)
            else:
                lo = (~rdat[ii])%256

        if param['end']%2: # to support odd number end address
            sum += lo
            sum %= 256*128
            print '0x%04x:' % (param['start']+ii),
            print '%02x => %02x' % (rdat[ii],lo)

        print '0x%04x (%d)' % (sum,sum)
        print '0x%04x => 0x%04x' % ((-sum)%(256*128),(~(-sum))%(256*256))


    def nvmargv (me, argvlst):
        """
        parse argvlst
        nvm(cmd)
            prog
            comp
            segm
            intr
        create expcod
        get options
            block= : block_num if block
        """
        param = me.get_data_list (argvlst)
#       print param
        if argvlst[0].find('prog',3)==3:
            me.nvmprog (param)

        elif argvlst[0].find('comp',3)==3:
            me.nvmcomp (param)

        elif argvlst[0].find('segm',3)==3: # segmented prog/comp
            me.nvmsegm (param)

        elif argvlst[0].find('intr',3)==3: # interleaved prog/comp
            me.nvmintr (param)

        elif argvlst[0].find('sum15',3)==3: # 15-bit summation
            me.nvmsum15 (param)

        else:
            print "nvm command not recognized,", argvlst[0]


    def show_mismatch (me, adr, dat, exp, num, limit=50):
        """
        for counting number of mismatch
        and show mismatch messages
        """
        if dat != exp:
            if num == limit: print 'suppress further display...',
            elif num < limit: print
            if num  < limit: print '0x%04X : %02X %c (!=%02X)' \
               % (adr, dat, chr(dat) if chr(dat)>' ' and dat<128 else ' ', exp),
            return 1
        else:
            return 0

        
    def nvm_block_read (me, addr, cnt, block=32):
        """
        """
        rdat = []
        me.nvmset (addr)
        for xx in range(addr,addr+cnt,block):
            rem = addr + cnt - xx
            rcnt = block if rem >= block else rem
            rdat += me.nvmrx (rcnt)
        return rdat

        
    def nvm_block_chk (me, addr, expcod, block=256, mismatch=0):
        """
        check block-by-block
        byte-by-byte if block=1
        """
        me.nvmset (addr)
        for xx in range(addr,addr+len(expcod),block):
            rem = addr + len(expcod) - xx
            rcnt = block if rem >= block else rem
            rdat = me.nvmrx (rcnt)
            for yy in range(len(rdat)):
                mismatch += me.show_mismatch (yy+xx, rdat[yy], expcod[yy+xx-addr], mismatch)

        end = addr+len(expcod)
        assert end==xx+rem, ('end address calc error', end, xx, rem)
#       [addr_l,addr_h] = me.sfrri (me.sfr.OFS,2)
#       assert (addr_l+addr_h*256) & me.sfr.nvmmsk == end, \
#              'SFR(DEC,OFS) error, 0x%02x%02x' % (addr_h,addr_l)
        me.sfrwx (me.sfr.DEC, [end>>8]) # clear ACK
        return mismatch


    def nvm_prog_block (me, addr, wrcod, rawsz, block=256, hiv=0, note=True):
        """
        program the in-byte array 'wrcod' into NVM block-by-block
        SFR-by-CSP: limit block size by CSP buffer and dummy
        SFR-by-I2C: 100KHz or lower write for PROG timing
        byte-by-byte if block=1 (slowly write for PROG timing)
        # hiv=0 to emulate (won't switch VPP) and check
        """
        assert hiv>=0 and hiv<=1, "invalid 'hiv', %d" % hiv
        me.nvmset (addr)
        rlst = me.sfr.pre_prog (me, hiv, note)
        start = time.time ()
        for xx in range(0, len(wrcod), block):
            wcnt = block if xx+block < len(wrcod) else len(wrcod)-xx
            me.sfrwx (me.sfr.NVMIO, wrcod[xx:xx+wcnt])

        me.sfr.pst_prog (me, rlst)
        if note:
            print 'complete'
            print "%.1f sec" % (time.time () - start)

        end = addr+rawsz
#       [addr_l,addr_h] = me.sfrri (me.sfr.OFS,2)
#       assert (addr_l+addr_h*256) & me.sfr.nvmmsk == end, \
#              'SFR(DEC,OFS) error, 0x%02x%02x' % (addr_h,addr_l)
        me.sfrwx (me.sfr.DEC, [end>>8]) # clear ACK


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


