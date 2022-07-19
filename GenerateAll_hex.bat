rem  SPDX-License-Identifier: GPL-2.0
rem 
rem  Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
rem 
rem  Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
rem -------------------------------------------------------------------------

echo off

if not exist C:\Python37\python.exe (
echo ==================================================
echo  ERROR, PLEASE INSTALL PYTHON 3.7 
echo .
echo .
echo      press any key to open the installation folder, and run installer for %PROCESSOR_ARCHITECTURE%
echo ==================================================
timeout \T 3  
start https://www.python.org/downloads/release/python-379/

) else (
C:\Python37\python.exe .\py_scripts\GenerateAll.py openssl 0 palladium
)
timeout /T 100