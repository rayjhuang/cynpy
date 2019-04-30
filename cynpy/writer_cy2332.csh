#!/bin/csh

    set prog = -mcynpy.csp

### *** pre-start ***
### power-on the I2C-to-CC (CSP) bridge
### try the CSP bridge
### try the CSP target (DUT)
### ===============================================================================
### python -mcynpy.aardv sw
### python -mcynpy.isp   rev
### python -mcynpy.isp   d[ump]
### python -mcynpy.csp   q[uery]
### python -mcynpy.csp   rev
### python -mcynpy.csp   d[ump]
### python -mcynpy.csp 1 d[ump] b0 30
### python -mcynpy.csp   stop
### python -mcynpy.csp   nvm


### prepare the bin file for temporary
### ===============================================================================
#   set hexfile = ../cy2332r0_20180810/Objects/cy2332r0_20180810_016.hex
    set hexfile = ~/Desktop/project/can1112/cy2332r0_20180810/Objects/cy2332r0_20180810_016.hex
    ls $hexfile
    if ! -e $hexfile exit -1
    hex2bin.py $hexfile temp.bin


### stop MCU
### ===============================================================================
    python $prog stop
    echo $status
exit

### ES may be not fully trimmed but OSC. Complete the row of CP trim
### ===============================================================================
### python $prog prog_hex 1 940    ff 00 0a 00 00 ff
### python $prog prog_hex 1 944 ff 4d 00 0a 00 00
### python $prog prog_hex 1 94a    4d 00 0a 00 00 ff
    python $prog set_trim


### upload FW
### ===============================================================================
    python $prog upload temp.bin 1
### python $prog upload ..\fw\cy2311r3\Objects\cy2311r3_20180606.2.memh 1
### python $prog upload ..\fw\scp\phy20180605a_prl0605\scp\Objects\scp_20180613.2.memh 1


### compare
### ===============================================================================
    python $prog comp   temp.bin \
                                       900=CAN1112A-000 \
                                       910=AP4377-14L \
                                       33=\90 34=\09 35=\40 36=\E4 37=\93 38=\F5 39=\A2 3A=\80 3B=\FE \
                                       940=\00 941=\FF 942=\FF 943=\FF 944=\FF


### FT information
### writer information
### option table
### PDO table
### mapping table
### ===============================================================================
### python $prog prog_asc 1 910 CAN1112A28L_BIN1
    python $prog prog_str 1 930 PY188_`date +%y%m%d%H%M`
    python $prog prog_hex 1 960 02 08 00 00

### 2-PDO (5V/3A, 3.3-5.9V/3A, 15W)
    python $prog   prog_hex 1 970 2C 91 01 0A  3C 21 76 C0

### 4-PDO (5V/3A, 9V/2A, 3.3-5.9V/3A, 3.3-11V/2A, 18W)
### python $prog   prog_hex 1 970 2C 91 01 0A  C8 D0 02 00  3C 21 76 C0  28 21 DC C0
### python $prog   prog_hex 1 a20    10 FA        51 C2     01 EE        13 E8 C1 F4 21 F4 12 E4

### 2-PDO (5V/3A, 9V/3A, 27W)
### python $prog   prog_hex 1 970 2C 91 01 0A  2C D1 02 00

### 3-PDO (5V/3A, 9V/3A, 3.3-11V/3A, 27/33W)
### python $prog   prog_hex 1 970 2C 91 01 0A  2C D1 02 00  3C 21 DC C0
### python $prog   prog_hex 1 a20    10 FA        51 C2     01 EE 13 E8 C1 F4 11 F4 B2 E4
### python $prog   prog_hex 1 a20    10 FA        51 C2     01 EE 13 E8 C1 F4 21 F4 12 E4

### 5-PDO (3.5V/3A, 5V/3A, 6V/3A, 7.3V/3A, 10V/2.2A, 22W)
### python $prog   prog_hex 1 970 2C 19 01 0A  2C 91 01 00  2C E1 01 00  2C 49 02 00  DC 20 03 00
### python $prog   prog_hex 1 a20    10 AF        50 FA        01 2C        11 6D        C1 F4     11 F4 62 E4

### python $prog 1 prog_hex 1 98c 2C 19 01 0A  2C 91 01 00  2C E1 01 00  2C 49 02 00  DC 20 03 00
### python $prog 1 prog_hex 1 98c 2C 91 01 0A  2C 91 01 00  3C 21 76 C0
### python $prog 1 prog_hex 1 9a8 2C 91 01 0A  3C 21 76 C0


### fine-tune table
### ===============================================================================
    python $prog   prog_hex 1 a58 80 20


### reset MCU
### ===============================================================================
### python $prog write F7 01 01 01
### python $prog reset

    rm temp.bin

