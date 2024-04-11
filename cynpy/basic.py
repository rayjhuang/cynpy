
TRUE  = 1 # ACK, YES, success
FALSE = 0 # NAK, NO,  failed

import sys, string
global argv_hex, argv_dec

#print(len(sys.argv),len(argv_hex),len(argv_dec))

def chk_argument ():
    if len(sys.argv) < 2:
        print sys.argv
        f = open (sys.argv[0],'r')
        cmd = ''
        tst = 0
        for line in f:
            start = line.find ('sys.argv[')
            if line.find ('line')<0 and start>=0 and line.find (']==')>0:
                print line[start:].lstrip(),
            if line.find ('line')<0 and line.find ('% python')>=0:
                cmd += '\n' + ' '.join(line.split()[0:])
            if line.find ('line')<0 and line.find ('=basic_dispatch')>=0:
                tst += 1

        if tst>0:
            basic_path = '/'.join(__file__.replace('\\','/').split('/')[0:-1]) + '/basic.py'
            print basic_path, tst
            for gg in open (basic_path,'r'):
                if gg.find ('line')<0 and gg.find ('sys.argv[1]')>=0:
                    print gg,

        print 'ex:',
        print cmd if len(cmd) else '\n% '+sys.argv[0]
        f.close ()
        return FALSE
    else:
        global argv_hex, argv_dec
        argv_hex = []
        argv_dec = []
        for xx in sys.argv:
            if len(xx) > 0:
                argv_hex += [int(xx,16)] if all (yy in '+-/^%' + string.hexdigits for yy in xx) else [xx]
                argv_dec += [int(xx,10)] if all (yy in '+-/^%' + string.digits    for yy in xx) else [xx]
        return TRUE

def pop_argument (): # remove ARGV[1]
    global argv_hex, argv_dec
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    argv_hex = [argv_hex[0]] + argv_hex[2:]
    argv_dec = [argv_dec[0]] + argv_dec[2:]


def sfr_vars (tstmst,arg2="",arg3=""):
    if arg2=='':
        print "\n".join("{!r}:{!r}".format(j,k) for j,k in \
                   vars(tstmst.sfr).items())
    elif arg3=='':
        print type(vars(tstmst.sfr)[arg2]), \
                   vars(tstmst.sfr)[arg2]
    elif arg3=='hexlist':
       print ['%02x' % xx for xx in \
                      vars(tstmst.sfr)[arg2]] # vars trimsfr hexlist
    elif arg3=='hex':
       print '%02x' % vars(tstmst.sfr)[arg2] # vars revid hex
    elif arg3=='str':
       print vars(tstmst.sfr)[arg2] # vars name str

    if arg3=='sfr':
        for ii in range(16):
            print '0x%02x:' % (argv_hex[2]/16*16+ii), tstmst.sfr.query_sfr (argv_hex[2]/16*16+ii)


def burst_write (tstmst):
    '''
    elif sys.argv[1]=='write'  : print tstmst.sfrwx (argv_hex[2],argv_hex[3:])
    elif sys.argv[1]=='w'      : tstmst.multi_write (sys.argv[2:])
    '''
    if len(sys.argv)>=3:
        if len(sys.argv[2].split('='))==2:
            tstmst.multi_write (sys.argv[2:])
        elif len(sys.argv)==3:
            print tstmst.sfrwx (argv_hex[2],[])
        else:
            print tstmst.sfrwx (argv_hex[2],argv_hex[3:])
    else:
        print 'ERROR: number of argument'


def burst_read (tstmst):
    '''
    elif sys.argv[1]=='read'   : print '0x%02x' % tstmst.sfrrx (argv_hex[2],1)[0]
    elif sys.argv[1]=='burst_read'  : print ['0x%02x' % xx for xx in \
                                            tstmst.sfrrx (argv_hex[2],argv_dec[3])]
    '''
    if   len(sys.argv)==3: print ['0x%02x' % xx for xx in tstmst.sfrrx (argv_hex[2],1)]
    elif len(sys.argv)==4: print ['0x%02x' % xx for xx in tstmst.sfrrx (argv_hex[2],argv_dec[3])]
    else:                  print 'ERROR: number of argument'


def scope_sfr (tstmst):
    if   len(sys.argv)==3 : tstmst.scope_sfr (argv_hex[2],1)
    elif len(sys.argv)==4 : tstmst.scope_sfr (argv_hex[2],argv_dec[3])
    elif len(sys.argv)==5 : tstmst.scope_sfr (argv_hex[2],argv_dec[3],argv_dec[4])
    else: print 'ERROR: number of argument'


def basic_dispatch (tstmst):
    rtn = sys.argv[1]
    if   sys.argv[1]=='rev'    : sfr_vars (tstmst,'name','str')
    elif sys.argv[1]=='sfr'    : sfr_vars (tstmst,sys.argv[2],'sfr')
    elif sys.argv[1]=='vars'   : sfr_vars (tstmst,sys.argv[2] if len(sys.argv)>2 else "", \
                                                  sys.argv[3] if len(sys.argv)>3 else "");
    elif sys.argv[1]=='adc'    : print tstmst.get_adc10 (argv_hex[2])
    elif sys.argv[1]=='read'   : burst_read (tstmst)
    elif sys.argv[1]=='write'  : burst_write (tstmst)
    elif sys.argv[1]=='loopw'  : tstmst.loop_write  (sys.argv[2:])
    elif sys.argv[1]=='loopwr' : tstmst.loop_w_r    (sys.argv[2:])
    elif sys.argv[1]=='loopr1' : tstmst.loop_read_1 (sys.argv[2:])
    elif sys.argv[1]=='loopr2' : tstmst.loop_read_2 (sys.argv[2:])

    elif sys.argv[1]=='scope_sfr' : scope_sfr (tstmst)
    elif sys.argv[1]=='scope_adc' : tstmst.scope_adc (argv_hex[2])

    elif sys.argv[1]=='fill'   : tstmst.pg0_fill (argv_dec[2],argv_hex[3],argv_hex[4])
    elif sys.argv[1]=='pg0'    : tstmst.pg0_form (argv_dec[2])
        
    elif sys.argv[1]=='d' or \
         sys.argv[1]=='dump'   : # def sfr_form (me, adr, cnt=16):
        if   len(sys.argv)==2  : tstmst.sfr_form (0x80,0x80)
        elif len(sys.argv)==3  : tstmst.sfr_form (argv_hex[2],0x10)
        else                   : tstmst.sfr_form (argv_hex[2],argv_hex[3])
    elif sys.argv[1].find('nvm',0)==0: # def nvm_form (me, ofs, cnt):
        if   sys.argv[1].find('prog',3)==3 \
          or sys.argv[1].find('comp',3)==3 \
          or sys.argv[1].find('segm',3)==3 \
          or sys.argv[1].find('intr',3)==3 \
          or sys.argv[1].find('sum15',3)==3 \
          or len(sys.argv[1])>3 : tstmst.nvmargv (sys.argv[1:])
        elif   len(sys.argv)==2 : tstmst.nvm_form (0x900,0x80)
        else: # >2
            if len(sys.argv)==3 : tstmst.nvm_form (argv_hex[2],0x80)
            else                : tstmst.nvm_form (argv_hex[2],argv_hex[3])

    elif sys.argv[1]=='stop'   : print tstmst.sfrwx (0xBC,[8]) # stop MCU
    elif sys.argv[1]=='reset'  : print tstmst.sfrwx (0xF7,[1,1,1]) # reset MCU

    elif sys.argv[1]=='shift'  : tstmst.shift_osc (argv_dec[2])
    elif sys.argv[1]=='trim'   : tstmst.set_trim ()
    elif sys.argv[1]=='get_trim' : print ['%02x' % xx for xx in tstmst.get_trim ()]

    elif sys.argv[1]=='prog_raw' : tstmst.nvm_prog_raw_block (argv_hex[2:] if len(sys.argv)>3 else \
                                                                map(ord,list(sys.argv[2])))
    elif sys.argv[1]=='dnload' : tstmst.nvm_download (sys.argv[2])
    elif sys.argv[1]=='burst'  : tstmst.nvm_upload_burst (sys.argv[2],argv_hex[3])
    elif sys.argv[1]=='test'   : tstmst.test (sys.argv[2:])
    else: rtn = 'none'
    return rtn


def tstmst_func (tstmst, dispatcher=basic_dispatch):
    if dispatcher (tstmst)=='none':
        line_no = 1
        f = open (sys.argv[1],'r')
        for line in f:
            line_split = []
            ptr = line.find('#')
            if ptr==0:
                if line[ptr+1]=='#': print '\n', line.split('\n')[0]
            elif ptr>0: line_split = line[0:ptr].split()
            else:       line_split = line.split()
            if len(line_split):
                print 'CMD', line_no, ':', line_split
                sys.argv[1:] = line_split
                chk_argument ()
                assert dispatcher (tstmst)!='none', 'ERROR: command not found'
            line_no += 1

