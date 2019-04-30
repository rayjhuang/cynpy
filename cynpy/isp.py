
if __name__ == '__main__':
    '''
    % python isp.py [cmd] [argv2] [...]
    % python isp.py rev
    % python isp.py write bc 8
    '''
    import i2c
    i2cmst = i2c.choose_master ()

    import sys, time
    import cynpy.basic as cmd
    if not cmd.no_argument ():
        if i2cmst:
            if sys.argv[1]=='ams':
                import cynpy.KBHit as KBHit
                kb = KBHit.KBHit ()
                def check_kb ():
                    return ord(kb.getch() if kb.kbhit() else '\x00')
                import cynpy.ams as ams
                tstmst = ams.ams(i2cmst, 0x70, check_kb, time.sleep, 1)
                '''
                enable auto-TX/RX-GoodCRC
                recover auto-TX/RX-GoodCRC setting
                '''
                tstmst.prltx.msk (0xff, 0x88) # enable auto-TX/RX-GoodCRC
                print '[AMS_RX]'
                while tstmst.main_loop () != 27:
                    pass

                print '[ESC]'
                tstmst.prltx.pop () # recover PRLTX settings

            else:
                import sfrmst
                tstmst = sfrmst.tsti2c(busmst=i2cmst, deva=0x70)
                cmd.tstmst_func (tstmst)
        else:
            raise 'I2C master not found'
