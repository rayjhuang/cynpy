
from aardvark_py import *
from i2c import *

class aardvark:
    def __init__ (me, p=-1):
        me.handle = 0
        if p >= 0:
            me.openChannel (p)

    def __del__ (me):
        if me.handle > 0:
            aa_close (me.handle)

    def openChannel (me, p):
        (number, ports, unique_ids) = aa_find_devices_ext(16, 16)
        if number > p:
            me.handle = aa_open (ports[p])
            if me.handle > 0:
                pass
            else:
                print 'Unable to open Aardvark device on port %d' % (p)
                print 'Error code = %d' % (me.handle)
        elif number > 0:
            print 'port', p, 'not found'
        else:
            print 'no AARDVARK port found'

    def enum (me, rpt=FALSE):
        (number, ports, unique_ids) = aa_find_devices_ext(16, 16)
        if rpt:
            print number, 'AARDVARK', 'ports' if number>1 else 'port', 'found'
            for xx in ports:
                print 'port %d' % (xx & ~AA_PORT_NOT_FREE),
                if xx & AA_PORT_NOT_FREE:
                    print 'is busy, skipped!!'
                else:
                    print 'v'*10
                    dev = aardvark(xx)
                    dev.aaShowVersion ()
        return number

    def aaShowVersion (me):
        assert me.handle > 0, 'no AARDVARK device opened'
        (sta, aaVer) = aa_version (me.handle)
        if (sta==AA_OK):
            print "struct AardvarkVersion {"
            print "\tsoftware: %x"      % aaVer.software
            print "\tfirmware: %x"      % aaVer.firmware
            print "\thardware: %x"      % aaVer.hardware
            print "\tsw_req_by_fw: %x"  % aaVer.sw_req_by_fw
            print "\tfw_req_by_sw: %x"  % aaVer.fw_req_by_sw
            print "\tapi_req_by_sw: %x" % aaVer.api_req_by_sw
            print "};"
        else:
            print "aa_version () failed!"

    def aaShowTargetPowerSta (me, sta):
        if   (sta==AA_TARGET_POWER_NONE):
            print "AA_TARGET_POWER_NONE %d" %sta
        elif (sta==AA_TARGET_POWER_BOTH):
            print "AA_TARGET_POWER_BOTH %d" %sta
        elif (sta==AA_INCOMPATIBLE_DEVICE):
            print "AA_INCOMPATIBLE_DEVICE %d" %sta
        else:
            print "aa_target_power failed! %d" %sta

    def aaSwitchTargetPower (me):
        assert me.handle > 0, 'no AARDVARK device opened'
        sta = aa_target_power (me.handle, AA_TARGET_POWER_QUERY)
        print 'QUERY:', aa_status_string (sta)
        if   (sta==AA_TARGET_POWER_BOTH):
            me.aaShowTargetPowerSta (aa_target_power (me.handle, AA_TARGET_POWER_NONE))
        elif (sta==AA_TARGET_POWER_NONE):
            me.aaShowTargetPowerSta (aa_target_power (me.handle, AA_TARGET_POWER_BOTH))
        else:
            print "TargetPowerSwitch failed! %d" %sta

    def aaSwitchPullup (me, ask): # '0' to ask, other for new setting
        assert me.handle > 0, 'no AARDVARK device opened'
    #   AA_I2C_PULLUP_QUERY
    #   AA_I2C_PULLUP_NONE
    #   AA_I2C_PULLUP_BOTH
        print aa_status_string (aa_i2c_pullup (me.handle, ask))
        # 0: none
        # others: OK


class aardvark_i2c (aardvark, i2c):
    def __init__ (me, p=-1):
        aardvark.__init__(me, p)
        if me.handle > 0:
            aa_configure (me.handle, AA_CONFIG_GPIO_I2C) # Ensure that the subsystem is enabled

    def baud (me, ask=0): # '0' to ask, other for new setting
        if not me.handle > 0: return 0 # no AARDVARK device opened'
        return aa_i2c_bitrate (me.handle, ask)

    def read (me, dev, adr, bycnt, rpt=FALSE): # SMB read
        '''
        '''
        if not me.handle > 0: return [] # no AARDVARK device opened'
        aa_i2c_write (me.handle, dev, AA_I2C_NO_STOP, array('B',[adr]))
        (r_cnt,r_dat) = aa_i2c_read (me.handle, dev, AA_I2C_NO_FLAGS, bycnt)
        if rpt:
            assert r_cnt == bycnt, 'I2C read failed, cnt:%d, exp:%d' \
                                                   % (r_cnt,bycnt)
            print '0x%02X: ' % adr,
            print (r_cnt,r_dat)
        return r_dat.tolist()

    def i2cw (me, wdat): # I2C write
        if not me.handle > 0: return 0 # no AARDVARK device opened'
        assert len(wdat) > 0, 'empty write data is not valid'
        if len(wdat) == 1:
            wdat += [0]
        return aa_i2c_write (me.handle, wdat[0], AA_I2C_NO_FLAGS, array('B',wdat[1:]))


class aardvark_spi (aardvark):
    def __init__ (me, p=-1):
        aardvark.__init__(me, p)
        if me.handle > 0:
            aa_configure (me.handle, AA_CONFIG_SPI_I2C) # Ensure that the subsystem is enabled
            aa_spi_configure (me.handle, 0, 0, AA_SPI_BITORDER_MSB) # Setup the clock phase

    def baud (me, ask=0): # '0' to ask, other for new setting
        if not me.handle > 0: return 0 # no AARDVARK device opened'
        return aa_spi_bitrate (me.handle, ask) # Set the bitrate, [125,8000] KHz

    def spix (me, wdat): # SPI transfer
        if not me.handle > 0: return 0 # no AARDVARK device opened'
        assert len(wdat) > 0, 'empty write data is not valid'
        rdat = [xx%256 for xx in range(len(wdat))]
        return aa_spi_write (me.handle, array('B',wdat), array('B',rdat))

    def read (me, cmd, adr, bycnt): # SPI read
        (r_cnt,r_dat) = me.spix ([cmd] + \
                                 [(adr >> 16) & 0xff, (adr >> 8) & 0xff, adr & 0xff] + \
                                 [xx%256 for xx in range(bycnt)])
        if (r_cnt < 0):
            print "error: %s\n" % aa_status_string(count)
            return []
        elif (r_cnt != bycnt+4):
            print "error: read %d bytes (expected %d)" % (r_cnt-4, bycnt)

        return r_dat[4:r_cnt].tolist()



if __name__ == '__main__':

    def test_only ():
        aa = aardvark_i2c(0)
        print 'query:', aa_configure (aa.handle, AA_CONFIG_QUERY)
        print aa_gpio_direction (aa.handle, 0x38)
        print aa_gpio_set (aa.handle, 0x38)
        print aa_gpio_get (aa.handle)
        print aa_gpio_set (aa.handle, 0x00)
        print aa_gpio_get (aa.handle)

    def test_spi_r ():
        for xx in aardvark_spi(0).read ( \
                           int(sys.argv[2],16), \
                           int(sys.argv[3],16), \
                           int(sys.argv[4])): print '0x%02X' % xx
        
    from basic import *
    if not no_argument ():
        if   sys.argv[1]=='ver'   : aardvark(0).aaShowVersion ()
        elif sys.argv[1]=='enum'  : aardvark().enum (rpt=TRUE)
        elif sys.argv[1]=='sw'    : aardvark(0).aaSwitchTargetPower ()
        elif sys.argv[1]=='pull'  : aardvark(0).aaSwitchPullup (int(sys.argv[2]))
        elif sys.argv[1]=='test'  : test_only ()

        elif sys.argv[1]=='spi_b' : print aardvark_spi(0).baud (argv_dec[2]), 'KHZ'
        elif sys.argv[1]=='spi_x' : print aardvark_spi(0).spix (argv_hex[2:])
        elif sys.argv[1]=='spi_r' : test_spi_r ()

        else: print "command not recognized"
