rem  SPDX-License-Identifier: GPL-2.0
rem 
rem  Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
rem 
rem  Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
rem -------------------------------------------------------------------------

echo off

rem Check Python version
call .\CheckPythonVersion.bat
if errorlevel 1 exit /b 1

cd py_scripts
python UpdateInputsBinaries_Arbel_A1_SVB.py
cd ..
timeout /T 100