
TRUE  = 1 # ACK, YES, success
FALSE = 0 # NAK, NO,  failed

import sys, string

global argv_hex, argv_dec
argv_hex = []
argv_dec = []
for xx in sys.argv:
    if len(xx) > 0:
        argv_hex += [int(xx,16)] if all (yy in '+-*/^%' + string.hexdigits for yy in xx) else [xx]
        argv_dec += [int(xx,10)] if all (yy in '+-*/^%' + string.digits    for yy in xx) else [xx]


def pop_argument ():
    global argv_hex, argv_dec
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    argv_hex = [argv_hex[0]] + argv_hex[2:]
    argv_dec = [argv_dec[0]] + argv_dec[2:]


def no_argument ():
    if len(sys.argv) < 2:
        f = open (sys.argv[0],'r')
        cmd = ''
        for line in f:
            start = line.find ('sys.argv[')
            if line.find ('line')<0 and start>=0 and line.find (']==')>0:
                print line[start:].lstrip(),
            if line.find ('line')<0 and line.find ('% python')>=0:
                cmd += '\n' + ' '.join(line.split()[0:])
            if line.find ('line')<0 and line.find ('tstmst_func')>=0: # if invoke tstmst_func()
                basic_path = '/'.join(__file__.replace('\\','/').split('/')[0:-1]) + '/basic.py'
                print basic_path
                for gg in open (basic_path,'r'):
                    if gg.find ('line')<0 and gg.find ('sys.argv[')>=0 and gg.find (']==')>0:
                        print gg,

        print 'ex:',
        print cmd if len(cmd) else '\n% '+sys.argv[0]
        f.close ()
        return TRUE
    else:
        return FALSE


def tstmst_func (tstmst):
    if   sys.argv[1]=='rev'   : print tstmst.sfr.name
    elif sys.argv[1]=='sfr'   : print tstmst.sfr.query_sfr (argv_hex[2])
    elif sys.argv[1]=='adc'   : print tstmst.get_adc10 (argv_hex[2])
    elif sys.argv[1]=='read'  : print '0x%02x' % tstmst.sfrrx (argv_hex[2],1)[0]
    elif sys.argv[1]=='wrx'   : print tstmst.sfrwx (argv_hex[2],argv_hex[3:])
    elif sys.argv[1]=='w' or \
         sys.argv[1]=='write' : tstmst.multi_sfr_write (sys.argv[2:])
    elif sys.argv[1]=='loopr' : tstmst.loopr (sys.argv[2:])
    elif sys.argv[1]=='loopw' : tstmst.loopw (sys.argv[2:])

    elif sys.argv[1]=='scope_sfr' : tstmst.scope_sfr (argv_hex[2])
    elif sys.argv[1]=='scope_adc' : tstmst.scope_adc (argv_hex[2])

    elif sys.argv[1]=='d' or \
         sys.argv[1]=='dump'  : # show SFR
        if   len(sys.argv)==2:  tstmst.sfr_form (0x80,0x80)
        elif len(sys.argv)==3:  tstmst.sfr_form (argv_hex[2],0x10)
        else:                   tstmst.sfr_form (argv_hex[2],argv_hex[3])
    elif sys.argv[1]=='nvm'   : # show OTP header
        if   len(sys.argv)==2:  tstmst.nvm_form (0x900,0x80)
        elif len(sys.argv)==3:  tstmst.nvm_form (argv_hex[2],0x80)
        else:                   tstmst.nvm_form (argv_hex[2],argv_hex[3])

    elif sys.argv[1]=='stop'  : print tstmst.sfrwx (0xBC,[8]) # stop MCU
    elif sys.argv[1]=='reset' : print tstmst.sfrwx (0xF7,[1,1,1]) # reset MCU

    elif sys.argv[1]=='shift'    : tstmst.shift_osc (argv_dec[2])
    elif sys.argv[1]=='trim'     : tstmst.set_trim ()
    elif sys.argv[1]=='get_trim' : print ['0x%02x' % xx for xx in tstmst.get_trim ()]

    elif sys.argv[1]=='prog_hex' : tstmst.nvm_prog (argv_hex[3],argv_hex[4:],argv_hex[2])
    elif sys.argv[1]=='prog_asc' : tstmst.nvm_prog (argv_hex[3],map(ord,list(sys.argv[4])),argv_hex[2])
    elif sys.argv[1]=='prog_str' : tstmst.nvm_prog_block ( \
                                                    argv_hex[3],map(ord,list(sys.argv[4])),len(sys.argv[4]),argv_hex[2])
    elif sys.argv[1]=='prog_raw' : tstmst.nvm_prog_raw_block (argv_hex[2:] if len(sys.argv)>3 else \
                                                                map(ord,list(sys.argv[2])))
    elif sys.argv[1]=='dnload'   : tstmst.nvm_download (sys.argv[2])
    elif sys.argv[1]=='upload'   : tstmst.nvm_upload_block (sys.argv[2],argv_hex[3])
    elif sys.argv[1]=='burst'    : tstmst.nvm_upload_burst (sys.argv[2],argv_hex[3])
    elif sys.argv[1]=='comp'     : tstmst.nvm_compare (sys.argv[2:])
    elif sys.argv[1]=='test'     : tstmst.test ()
    else: print "command not recognized,", sys.argv[1]
