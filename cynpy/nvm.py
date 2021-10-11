
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
        else:
            assert len(param['data'])>0, 'no data_list to do'

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
        print 'check from 0x%04x to 0x%04x' % (param['start'],param['end']-1),
        start = time.time ()
        mismatch = 0
        if 'blockr' in param and param['blockr']=='':
            mismatch = me.nvm_block_chk (param['start'], param['data'])
        else:
            block = int(param['blockr']) if 'blockr' in param else 1
            assert block>0, 'invalid blockr %d' % block
            mismatch = me.nvm_block_chk (param['start'], param['data'], block)

        print ('\nmismatch: %s' % (mismatch)) if mismatch else 'complete'
        print '%.1f sec' % (time.time () - start)


    def nvmprog (me, param):
        """
        hiv=0 to emulate (won't switch VPP) and check
        hiv=1 to byte-programming
        hiv=2 to byte-programming and check
        """
        hiv = 0 if not 'hiv' in param else int(param['hiv'])
        assert hiv>=0 and hiv<=2, 'invalid hiv %d' % hiv
        if 'blockw' in param:
            if param['blockw']=='':
                 print 'default block size'
            else:
                blockw = int(param['blockw'])
                assert blockw>0, 'invalid blockw %d' % blockw
            raise NotImplementedError()
        else:
            me.nvm_prog_byte (param['start'], param['data'], hiv>0)

        if hiv==0 or hiv==2:
            me.nvmcomp (addr, param)


    def nvmargv (me, argvlst):
        """
        parse argvlst
        nvm(cmd)
            prog
            comp
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

        else:
            print "nvm command not recognized,", argvlst[0]


    def show_mismatch (me, adr, dat, exp, num, limit=50):
        """
        for counting number of mismatch
        and show mismatch messages
        """
        if dat != exp:
            if num == limit: print 'suppress further display...',
            if num  < limit: print '\n0x%04X : %02X %c (!=%02X)' \
               % (adr, dat, chr(dat) if chr(dat)>' ' and dat<128 else ' ', exp),
            return 1
        else:
            return 0

        
    def nvm_block_chk (me, start, expcod, block=256, mismatch=0):
        """
        check block-by-block
        byte-by-byte if block=1
        """
        end = start+len(expcod)
        me.nvmset (start)
        for xx in range(start,start+len(expcod),block):
            rem = start + len(expcod) - xx
            rcnt = block if rem >= block else rem
            rdat = me.nvmrx (rcnt)
            for yy in range(len(rdat)):
                mismatch += me.show_mismatch (yy+xx, rdat[yy], expcod[yy+xx-start], mismatch)

        assert end==xx+rem, ('end address calc error', end, xx, rem)
#       [addr_l,addr_h] = me.sfrri (me.sfr.OFS,2)
#       assert (addr_h-0x80)*256+addr_l == end, \
#              'SFR(DEC,OFS) error, 0x%02x%02x' % (addr_h,addr_l)
        me.sfrwx (me.sfr.DEC, [end>>8]) # clear ACK
        return mismatch


    def nvm_prog_byte (me, adr, wlst, hiv=0):
        """
        program @adr those in list 'wlst' byte-by-byte
        slowly write for PROG timing
        # hiv=0 to emulate (won't switch VPP) and check
        """
        assert hiv>=0 and hiv<=1, 'invalid hiv'
        me.nvmset (adr)
        rlst = me.sfr.pre_prog (me, hiv)
        for xx in range(len(wlst)):
            me.sfrwx (me.sfr.NVMIO, [wlst[xx]])
        me.sfr.pst_prog (me, rlst)
        time.sleep(1) # wait for voltage revovery

        dec = me.sfrrx (me.sfr.DEC, 1)[0]
        me.sfrwx (me.sfr.DEC, [(me.sfr.nvmmsk >> 8) & dec]) # clear ACK


    def nvm_prog_block (me, addr, wrcod, rawsz, hiv=0, block=256):
        """
        program the in-byte array 'wrcod' into NVM block-by-block
        SFR-by-CSP: limit block size by CSP buffer and dummy
        SFR-by-I2C: 100KHz write for PROG timing
        """
        assert block > 0, 'block size must be positive'
        me.nvmset (addr)
        rlst = me.sfr.pre_prog (me, hiv)
        start = time.time ()

        for xx in range(0, len(wrcod), block):
            wcnt = block if xx+block <= len(wrcod) else len(wrcod)-xx
            me.sfrwx (me.sfr.NVMIO, wrcod[xx:xx+wcnt])

        me.sfr.pst_prog (me, rlst)
        print "%.1f sec" % (time.time () - start)
        time.sleep(1) # wait for voltage revovery

        dec = me.sfrrx (me.sfr.DEC, 1)[0]
        me.sfrwx (me.sfr.DEC, [(me.sfr.nvmmsk >> 8) & dec]) # clear ACK

        ofs = me.sfrrx (me.sfr.OFS, 1)[0]
        endadr = (ofs+dec*256) & me.sfr.nvmmsk
        print ('ERROR: 0x%04x' % (endadr)) \
        if endadr != (addr + rawsz) & me.sfr.nvmmsk else 'complete'


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


