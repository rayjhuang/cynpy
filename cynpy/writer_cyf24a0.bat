

REM python -B cynpy\csp.py stop
REM python -B cynpy\csp.py trim
    python -B cynpy\csp.py nvmsegm 0   hiv=2 intr=7 ..\CYF24A0_Tmk0a170.bin
    python -B cynpy\csp.py nvmprog 930 hiv=2 \PY1124%DATE:~2,2%%DATE:~5,2%%DATE:~8,2%%TIME:~0,2%%TIME:~3,2%

