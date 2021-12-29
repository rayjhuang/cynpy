
if __name__ == '__main__':
    '''
    % python csp.py [cmd|SOP*] [cmd] [...]
    % python csp.py q[uery]
    % python csp.py 1 read bb
    '''
    import i2c
    i2cmst = i2c.choose_master ()

    import sys
    import basic as cmd
    if not cmd.no_argument ():
        if i2cmst:
            import canm0
            if sys.argv[1]=='q' or \
               sys.argv[1]=='query' : # query SOP*
                cspbdg = canm0.canm0(i2cmst, 0x70) # no SOP*
                print cspbdg.probe (1)
            else:
                if cmd.argv_hex[1]>0 and cmd.argv_hex[1]<=5: # assign SOP* by command line
                    cspbdg = canm0.canm0(i2cmst, 0x70, cmd.argv_hex[1])
                    cmd.pop_argument ()
                else:
                    cspbdg = canm0.canm0(i2cmst, 0x70, 5)

                if len(sys.argv)==2 and sys.argv[1]=='scan': cspbdg.pass_band ()
                else:
                    import sfrmst
                    cspbdg.prltx.msk (0xff, 0x08) # enable auto-RX-GoodCRC
                    tstmst = sfrmst.tstcsp(cspbdg)
                    cmd.tstmst_func (tstmst)
                    cspbdg.prltx.pop ()
        else:
            raise 'I2C master not found'
