rem  SPDX-License-Identifier: GPL-2.0
rem
rem  Nuvoton IGPS: ECC Key Format Converter
rem
rem  Converts between PEM, DER, and BIN formats for ECDSA public keys
rem  Usage: ConvertKeyFormat.bat <input_file_path>
rem -------------------------------------------------------------------------

@echo off
setlocal enabledelayedexpansion

if not exist C:\Python37\python.exe (
    echo ==================================================
    echo  ERROR, PLEASE INSTALL PYTHON 3.7
    echo .
    echo .
    echo      Press any key to open the installation page
    echo ==================================================
    timeout /T 3
    start https://www.python.org/downloads/release/python-379/
    goto :end
)

if "%~1"=="" (
    echo ==================================================
    echo  ECC Key Format Converter
    echo ==================================================
    echo ==================================================
    goto :end
)

echo ==================================================
echo  ECC Key Format Converter
echo ==================================================
echo  Input: %~1
echo.

C:\Python37\python.exe .\py_scripts\ImageGeneration\GenerateKeyECC_fromKnownFile.py "%~1"

:end
timeout /T 5
