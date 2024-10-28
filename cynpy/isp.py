
if __name__ == '__main__':
    '''
    % python isp.py [cmd] [argv2] [...]
    % python isp.py rev
    % python isp.py write bc 8
    '''
    import sys
    import basic as cmd
    if cmd.chk_argument ():
        import i2c
        i2cmst = i2c.choose_master ()
        if i2cmst:
            if sys.argv[1]=='61':
                import sfrmst
                tstmst = sfrmst.tsti2c(busmst=i2cmst, deva=0x61)
                cmd.pop_argument ()
                cmd.tstmst_func (tstmst)

            else:
                import sfrmst
                tstmst = sfrmst.tsti2c(busmst=i2cmst, deva=0x70)
                cmd.tstmst_func (tstmst)

            i2cmst.__del__()

        else:
            raise 'I2C master not found'
