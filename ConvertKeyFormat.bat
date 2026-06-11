rem  SPDX-License-Identifier: GPL-2.0
rem
rem  Nuvoton IGPS: ECC Key Format Converter
rem
rem  Converts between PEM, DER, and BIN formats for ECDSA public keys
rem  Usage: ConvertKeyFormat.bat <input_file_path>
rem -------------------------------------------------------------------------

@echo off
setlocal enabledelayedexpansion

rem Check Python version
call CheckPythonVersion.bat
if errorlevel 1 goto :end

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

python .\py_scripts\ImageGeneration\GenerateKeyECC_fromKnownFile.py "%~1"

:end
timeout /T 5
