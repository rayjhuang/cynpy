    @ECHO OFF

    ECHO =A%1A=

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
    SET HEXFILE=z:\RD\Project\CAN1112\Ray\fw\vooc\vooc-v03.hex
    IF NOT EXIST %HEXFILE% GOTO USAGE

REM prepare the bin file for temporary
REM ===============================================================================
    python -B c:\Python27\Scripts\hex2bin.py %HEXFILE% temp.bin


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
    python %PROG% upload temp.bin 1

REM compare
REM ===============================================================================
    python %PROG%   comp temp.bin ^
                        900=CAN1112A-000 ^
                        910=AP43772-14L ^
                        33=\90 34=\09 35=\40 36=\E4 37=\93 38=\F5 39=\A2 3A=\80 3B=\FE

REM writer information
REM ===============================================================================
    python %PROG% prog_str 1 930 PY187_%DATE:~2,2%%DATE:~5,2%%DATE:~8,2%%TIME:~0,2%%TIME:~3,2%


REM reset MCU
REM ===============================================================================
REM python %PROG% wrx F7 01 01 01
REM python %PROG% reset

    DEL temp.bin

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
