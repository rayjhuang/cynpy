@echo off
rem Windows 7

    SET TOTALPHASEPATH=Y:\project\tools\TotalPhase
rem SET TOTALPHASEPATH=D:\TotalPhase
rem SET TOTALPHASEPATH=%CD%\..\..\tools\TotalPhase

rem SET MYPYPATH=%HOMEDRIVE%%HOMEPATH%\Dropbox\script\python
rem SET MYPYPATH=E:\Dropbox\script\python
rem SET MYPY=%MYPYPATH%\rapy

rem SET PYTHONPATH=%TOTALPHASEPATH%\aardvark-api-windows-i686-v5.13\python

    SET PYTHONPATH=%CD%;%TOTALPHASEPATH%\aardvark-api-windows-x86_64-v5.13\python

    dir/w %PYTHONPATH%
rem dir/w %MYPY%

    @PATH=%CD%;%PATH%
