
TRUE  = 1 # ACK, YES, success
FALSE = 0 # NAK, NO,  failed

class sfr11xx (object):
    '''
    sfr11xx class hierarchy
    -----------------------
            sfr1108
           /
    sfr11xx - sfr111x - sfr1110
                     \
                      sfr1112
    '''
    #############################################################################
    ## M51/CAN11XX common part                                                 ##
    WDTREL  = 0x86

    S0CON   = 0x98
    S0BUF   = 0x99

    IEN0    = 0xA8 ## IE in REG52.H
    IP0     = 0xA9
    S0RELL  = 0xAA

    IP      = 0xB8 ## R8051
    IEN1    = 0xB8 ## R80515
    S0RELH  = 0xBA

    IRCON   = 0xC0

    ADCON   = 0xD8
    I2CDAT  = 0xDA
    I2CADR  = 0xDB
    I2CCON  = 0xDC
    I2CSTA  = 0xDD

    SRST    = 0xF7

    TXCTL   = 0xb0
    FFCTL   = 0xb1
    FFIO    = 0xb2
    STA0    = 0xb3
    STA1    = 0xb4
    MSK0    = 0xb5
    MSK1    = 0xb6
    FFSTA   = 0xb7
    RXCTL   = 0xbb
    MISC    = 0xbc
    PRLS    = 0xbd
    PRLTX   = 0xbe
    GPF     = 0xbf

    I2CCMD  = 0xc1
    OFS     = 0xc2
    DEC     = 0xc3
    PRLRXL  = 0xc4
    PRLRXH  = 0xc5
    TRXS    = 0xc6
    REVID   = 0xc7

    OSCCTL  = 0xd4
    GPIOP   = 0xd5
    GPIOSL  = 0xd6
    GPIOSH  = 0xd7

    I2CCTL  = 0xc9
    I2CDEVA = 0xca
    I2CMSK  = 0xcb
    I2CDEV  = 0xcc
    I2CBUF  = 0xcd
    PCL     = 0xce
    NVMIO   = 0xcf

    CCRX    = 0xe6

    def __init__ (me, revid=0):
        me.bufsz = 34 # -byte FIFO
        me.name = ''
        me.revid = revid
        if revid:
            me.name = me.dict_id [revid]

    def get_reverse (me, org, nbit):
        ret = 0
        for xx in range(nbit):
            ret <<= 1
            if org%2: ret |= 1
            org >>= 1
        return ret

    def get_osc (me, org, delta):
        '''
        signed int 'delta' for plus/minus the orginal value
        '''
        raise NotImplementedError()

    def check (me, revid):
        for k,v in me.dict_id.iteritems():
            if k is revid:
                return TRUE
        return FALSE

    def query_sfr (me, something):
        if type(something) == int:
            return me.get_sfr_name (something)
        else:
            return me.get_sfr_name (-1, something)

    def get_sfr_name (me, adr, name=''):
        for k,v in list(vars(sfr11xx).iteritems()):
            if adr >= 0 and v == adr: return k
            if adr < 0 and k == name: return '0x%02X' % v
        return '' # not found



class sfr1108 (sfr11xx):

    ANACTL  = 0xd1
    AOPTL   = 0xd2
    AOPTH   = 0xd3

    TM      = 0xd9

    dict_id = {0x0a:'CAN1108', \
               0x1a:'CAN1111'}

    def __init__ (me, revid=0):
        super(sfr1108,me).__init__ (revid)
        me.inc = 1 # CAN1108 power-on I2CSLV in INC mode
        me.nbyte = 2
        me.dummy = 3
        me.nvmsz = 0x0a00
        me.nvmmsk = 0x0fff # address width
        me.trimsz = 2
        me.trimsfr = 0xd2
        me.trimnum = 8
        me.trimtable = 0x970

        me.sfr_osc = me.AOPTH

    def get_osc (me, org, delta):
        new = me.get_reverse (org, 5)
        if new > 15: new -= 32 # minus
        new += delta
        if new > 15: new = 15 # upper limit
        if new <-16: new =-16 # lower limit
        return org & 0xe0 | me.get_reverse (new, 5)

    def get_sfr_name (me, adr, name=''):
        for k,v in list(vars(sfr1108).iteritems()):
            if adr >= 0 and v == adr: return k
            if adr < 0 and k == name: return '0x%02X' % v
        return sfr11xx.get_sfr_name(me,adr,name)



class sfr111x (sfr11xx):

    RWBUF   = 0xd2

    ATM     = 0xd9

    P0MSK   = 0xde
    P0STA   = 0xdf

    COMPI   = 0xe1
    CMPSTA  = 0xe2
    SRCCTL  = 0xe3
    PWRCTL  = 0xe4
    PWR_V   = 0xe5

    CCCTL   = 0xe7

    DACCTL  = 0xf1
    DACEN   = 0xf2
    SAREN   = 0xf3

    DACV0   = 0xf8
    DACV1   = 0xf9
    DACV2   = 0xfa
    DACV3   = 0xfb
    DACV4   = 0xfc
    DACV5   = 0xfd
    DACV6   = 0xfe
    DACV7   = 0xff

    def __init__ (me, revid=0):
        super(sfr111x,me).__init__ (revid)
        me.sfr_osc = me.REGTRM0

    def get_osc (me, org, delta):
        new = (org & 0x3f) + delta
        if new > 31: new = 31
        if new <-32: new =-32
        return org & 0xc0 | new

    def get_sfr_name (me, adr, name=''):
        for k,v in list(vars(sfr111x).iteritems()):
            if adr >= 0 and v == adr: return k
            if adr < 0 and k == name: return '0x%02X' % v
        return sfr11xx.get_sfr_name(me,adr,name)



class sfr1110 (sfr111x):

    CMPOPT  = 0x9f

    CDCTL   = 0xa1
    CDVAL   = 0xa2
    PWR_I   = 0xa3
    PWMP    = 0xa4
    PWMD    = 0xa5
    PROCTL  = 0xa6
    PROSTA  = 0xa7
    
    CVCTL   = 0xab
    DTR     = 0xac
    DTF     = 0xad
    DDCTL   = 0xae
    DDBND   = 0xaf

    NVMCTL  = 0xd1 # CAN1110

    EXGP    = 0xd3 # CAN1110

    REGTRM0 = 0xe9
    REGTRM1 = 0xea
    REGTRM2 = 0xeb
    REGTRM3 = 0xec
    REGTRM4 = 0xed
    AOPT    = 0xee

    DACLSB  = 0xf6

    dict_id = {0x0b:'CAN1110A/B', \
               0x0c:'CAN1110C/D/E/F'}

    def __init__ (me, revid=0):
        super(sfr1110,me).__init__ (revid)
        me.inc = 0 # CAN1110 power-on I2CSLV in non-INC mode
        me.nbyte = 1
        me.dummy = 3
        me.nvmsz = 0x2000
        me.nvmmsk = 0x1fff # address width
        me.trimsz = 5
        me.trimsfr = 0xe9
        me.trimnum = 6
        me.trimtable = 0x940

    def get_sfr_name (me, adr, name=''):
        for k,v in list(vars(sfr1110).iteritems()):
            if adr >= 0 and v == adr: return k
            if adr < 0 and k == name: return '0x%02X' % v
        return sfr111x.get_sfr_name(me,adr,name)



class sfr1112 (sfr111x):

    DPDNCTL = 0xa1
    REGTRM0 = 0xa2
    REGTRM1 = 0xa3
    REGTRM2 = 0xa4
    REGTRM3 = 0xa5
    REGTRM4 = 0xa6
    AOPT    = 0xa7

    PWR_I   = 0xac
    PROVAL  = 0xad
    PROSTA  = 0xae
    PROCTL  = 0xaf

    GPIO5   = 0xd1

    GPIO34  = 0xd3

    CMPOPT  = 0xe8

    DACLSB  = 0xf4
    CVCTL   = 0xf5

    dict_id = {0x2a:'CAN1112AX', \
               0x2b:'CAN1112B0', \
               0x2c:'CAN1112B1', \
               0x2d:'CAN1112B2'}

    def __init__ (me, revid=0):
        super(sfr1112,me).__init__ (revid)
        me.inc = 0 # CAN1112 power-on I2CSLV in non-INC mode
        me.nbyte = 2
        me.dummy = 2
        me.nvmsz = 0x4200
        me.nvmmsk = 0x7fff # address width
        me.trimsz = 5 # bytes SFR
        me.trimsfr = 0xa2 # SFR start
        me.trimnum = 6 # entries MTT
        me.trimtable = 0x940 # base address in OTP

    def get_sfr_name (me, adr, name=''):
        for k,v in list(vars(sfr1112).iteritems()):
            if adr >= 0 and v == adr: return k
            if adr < 0 and k == name: return '0x%02X' % v
        return sfr111x.get_sfr_name(me,adr,name)
