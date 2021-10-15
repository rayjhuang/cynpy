

    python -B .\cynpy\csp.py stop
REM python -B .\cynpy\csp.py trim
    python -B .\cynpy\csp.py upload Y:\project\git\CY2332_R0\Release\cy2332r0.bin 1
    python -B .\cynpy\csp.py comp   Y:\project\git\CY2332_R0\Release\cy2332r0.bin ^
			     33=\90 34=\09 35=\40 36=\E4 37=\93 38=\F5 39=\A2 3A=\80 3B=\FE ^
			     900=CAN1110C-000 ^
			     910=CY2311S-16L ^
			     940=\00 941=\00 942=\00 943=\00 944=\00

    python -B .\cynpy\csp.py prog_str 1 930 PY2332%DATE:~2,2%%DATE:~5,2%%DATE:~8,2%%TIME:~0,2%%TIME:~3,2%

    python -B .\cynpy\csp.py prog_hex 1 960 02 28 00 00
    python -B .\cynpy\csp.py prog_hex 1 970 2C 91 01 0A  2C D1 02 00  3C 21 DC C0
    python -B .\cynpy\csp.py prog_hex 1 a20       10 FA        51 C2        01 EE  13 E8  C1 F4  11 F4  B2 E4

