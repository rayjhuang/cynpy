    @ECHO OFF

    ECHO =%1=

    SET PROG=
    IF NOT %2A == A     GOTO USAGE
    IF [%1] == []       GOTO DEFULT
    IF %1  == cynpy.csp GOTO START
    IF %1  == cynpy.isp GOTO START
    IF %1  ==  rapy.csp GOTO START
    IF %1  ==  rapy.isp GOTO START
    GOTO USAGE

:DEFULT
    SET PROG=cynpy.csp

:START
    SET PROG=-m%PROG%%1
REM SET HEXFILE=..\fw\cy2311r3\Objects\cy2311r3_x004.hex
REM SET HEXFILE=z:\RD\Project\CAN1112\Ray\fw\cy2332r0_20181024_033.hex
REM SET BINFILE=temp.bin
    SET BINFILE=y:\project\git\CY2332_R0\Release\cy2332r0.bin
    ECHO =%BINFILE%=
    IF NOT EXIST %BINFILE% GOTO USAGE

REM prepare the bin file for temporary
REM ===============================================================================
REM python -B c:\Python27\Scripts\hex2bin.py %HEXFILE% temp.bin

REM python %PROG% 1 w e7=00 bc=08 e4=02 e5=3e af=00 b0=00 be=07
REM python %PROG% 1 trim


REM stop MCU
REM ===============================================================================
    python %PROG% stop


REM ES may be not fully trimmed but OSC. Complete the row of CP trim
REM ===============================================================================
REM python %PROG% prog_hex 1 940    ff 00 0a 00 00 ff
REM python %PROG% prog_hex 1 944 ff 4d 00 0a 00 00
    python %PROG% trim

REM upload FW
REM ===============================================================================
    python %PROG% upload %BINFILE% 1
REM python %PROG% upload ..\fw\cy2311r3\Objects\cy2311r3_20180606.2.memh 1
REM python %PROG% upload ..\fw\scp\phy20180605a_prl0605\scp\Objects\scp_20180613.2.memh 1


REM compare
REM ===============================================================================
REM python %PROG%   comp %BINFILE% ^
REM                 900=CAN1112B-000 ^
REM                 33=\90 34=\09 35=\40 36=\E4 37=\93 38=\F5 39=\A2 3A=\80 3B=\FE ^
REM                 940=\00 941=\00 942=\00 943=\00 944=\00

    python %PROG%   comp %BINFILE% ^
                    900=CAN1110E-000 ^
                    910=CY2311-16L ^
                    940=\00 941=\00 942=\00 943=\00 944=\00

REM FT information
REM writer information
REM option table
REM PDO table
REM mapping table
REM ===============================================================================
REM python %PROG% prog_asc 1 910 CAN1112A28L_BIN1
    python %PROG% prog_str 1 930 PY187_%DATE:~2,2%%DATE:~5,2%%DATE:~8,2%%TIME:~0,2%%TIME:~3,2%
REM python %PROG% prog_hex 1 960 02 08 00 00
    python %PROG% prog_hex 1 960 02 28 00 00
REM python %PROG% prog_hex 1 960 06 08 08 00
REM python %PROG% prog_hex 1 960 06 2B 08 00

REM 2-PDO (5V/3A, 3.3-5.9V/3A, 15W/17.7W)
REM python %PROG%   prog_hex 1 970 2C 91 01 0A  3C 21 76 C0

REM 3-PDO (5V/3A, 9V/3A, 3.3-11V/3A, 27/33W)
    python %PROG% prog_hex 1 970 2C 91 01 0A  2C D1 02 00  3C 21 DC C0
    python %PROG% prog_hex 1 a20    10 FA        51 C2     01 EE  13 E8  C1 F4  11 F4  B2 E4
REM python %PROG% prog_hex 1 a20    10 FA        51 C2     01 EE  13 E8  C1 F4  21 F4  12 E4

REM 4-PDO (5V/3A, 9V/2A, 3.3-5.9V/3A, 3.3-11V/2A, 18W/22W)
REM python %PROG% prog_hex 1 970 2C 91 01 0A  C8 D0 02 00  3C 21 76 C0  28 21 DC C0
REM python %PROG% prog_hex 1 A20    10 FA        51 C2     01 EE        13 E8  C1 F4  11 F4  22 E4
REM python %PROG% prog_hex 1 A20    10 FA        51 C2     01 EE        13 E8  C1 F4  11 F4  62 E4

REM 6-PDO (5V/3A, 6V/3A, 7V/3A, 8V/2.75A, 9V/2.44A, 10V/2.2A, 22W)
REM python %PROG% prog_hex 1 970 2C 91 01 0A  2C E1 01 00  2C 31 02 00  13 81 02 00  F4 D0 02 00  DC 20 03 00
REM python %PROG% prog_hex 1 A20    10 FA        51 2C        01 5E        11 90        C1 C2        11 F4  62 E4


REM 3-PDO (5V/3A, 9V/2A, 3.3-21V/2A, ??W)
REM python %PROG%   prog_hex 1 970 2C 91 01 0A  C8 D0 02 00  28 21 A4 C1
REM python %PROG% 1 prog_hex 1 98C 2C 91 01 0A  C8 D0 02 00  28 21 A4 C1

REM 3+PDO (3V/3A, 5V/3A, 9V/3A, 3.3-11V/3A, 33W)
REM python %PROG% 1 prog_hex 1 98C 2C F1 00 0A  2C 91 01 00  2C D1 02 00  3C 21 DC C0
REM python %PROG% 1 prog_hex 1 A2E    10 96        50 FA        01 C2     13 E8  C1 F4  21 F4  12 E4


REM fine-tune table 0x0A58 : 70 21
REM ===============================================================================
REM python %PROG% prog_hex 1 a58 FF FF
REM python %PROG% prog_hex 1 a58 80 61


REM reset MCU
REM ===============================================================================
REM python %PROG% wrx F7 01 01 01
REM python %PROG% reset

REM DEL temp.bin

GOTO EXIT

:USAGE
ECHO NOTE:
ECHO 1. power-on the I2C-to-CC bridge
ECHO 2. try the bridge
ECHO 3. try the target (DUT)
ECHO ===============================================================================
ECHO python -mcynpy.aardv sw
ECHO python -mcynpy.isp   rev
ECHO python -mcynpy.isp   dump
ECHO python -mcynpy.csp   query
ECHO python -mcynpy.csp   rev
ECHO python -mcynpy.csp   dump
ECHO python -mcynpy.csp 1 dump b0 30
ECHO python -mcynpy.csp   stop
ECHO python -mcynpy.csp   nvm
ECHO python -mcynpy.csp   dnload otp.bin

:EXIT
