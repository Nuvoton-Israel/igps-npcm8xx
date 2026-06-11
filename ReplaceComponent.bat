rem  SPDX-License-Identifier: GPL-2.0
rem 
rem  Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
rem 
rem  Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
rem -------------------------------------------------------------------------

echo off

rem Check Python version
call CheckPythonVersion.bat
if errorlevel 1 exit /b 1

python .\py_scripts\GenerateAll.py openssl %1 partial
timeout /T 100