rem  SPDX-License-Identifier: GPL-2.0
rem 
rem  Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
rem 
rem  Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
rem -------------------------------------------------------------------------

:: Program Arbel EVB SPI0.CS0 flash. 
:: This tool works with Arbel EVB PCB X01 (blue board) and above. 
:: To use automation, make sure the following J2 header pins are populate with jumpers: 
::    > J2.3  & J2.4 : Port A.0; STRAP7 (BMC pins are at Hi-Z).  (** only on PCB version X01)
::    > J2.7  & J2.8 : Port A.2; STRAP5 (Rout BSP signals via Host SI2 pins). 
::    > J2.15 & J2.16: Port A.6; PORST_N (Power-On-Reset). 
:: * Make sure the relevent STRAP DIP-SWITCH are at OFF position. 

@echo off


SET FILE_TO_PROGRAM=".\py_scripts\ImageGeneration\output_binaries\Secure\Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_uboot.bin"

ECHO === PROGRAM  %FILE_TO_PROGRAM% =======

SET PIN_HIGH=1 1 
SET PIN_LOW=1 0
SET PIN_IN=0 0

SET STRAP7=0 
SET STRAP7_ASSERTED=-pin-set %STRAP7% %PIN_LOW%
SET STRAP7_RELEASE=-pin-set %STRAP7% %PIN_IN%

SET PORST_N=6
SET PORST_ASSERTED=-pin-set %PORST_N% %PIN_LOW%
SET PORST_RELEASE=-pin-set %PORST_N% %PIN_IN%

SET STRAP5=2
SET STRAP5_ASSERTED=-pin-set %STRAP5% %PIN_LOW%
SET STRAP5_RELEASE=-pin-set %STRAP5% %PIN_IN%


:: enter the EVB into tri-state 
echo.
echo.
echo ***************************************
echo **** Enter NPCM8mnx into tri-state ****
echo ***************************************
echo.
::Arbel_EVB_Automation -list 
.\py_scripts\ImageProgramming\Arbel_EVB_Automation.exe -open-desc "NPCM8mnx_Evaluation_Board A" %PORST_ASSERTED% %STRAP7_ASSERTED% -update -delay 10 %PORST_RELEASE% -update -delay 10
if NOT ERRORLEVEL 0 goto ERROR

:: program the flash with the file image. 32MB takes 1min ~ 6min (depend of flash and file content) 
echo.
echo.
echo **************************************
echo ****      Program the flash       ****
echo **************************************
echo.
::Arbel_EVB_FlashProg.exe -list 
.\py_scripts\ImageProgramming\Arbel_EVB_FlashProg.exe -open-desc "NPCM8mnx_Evaluation_Board B" -verify-on -pin-set 7 %PIN_LOW% -prog-file %FILE_TO_PROGRAM% 0 0 -1 -reset 
if NOT ERRORLEVEL 0 goto ERROR

:: exit the EVB from tri-state 
echo.
echo.
echo ********************************************
echo **** Exit tri-state and reset NPCM8mnx  ****
echo ********************************************
echo.
.\py_scripts\ImageProgramming\Arbel_EVB_Automation.exe -open-desc "NPCM8mnx_Evaluation_Board A" %PORST_ASSERTED% %STRAP5_ASSERTED% -update -delay 10 %PORST_RELEASE% -update
if NOT ERRORLEVEL 0 goto ERROR


::call TeraTerm_CLI_Builder.bat
::call SI2.bat
goto PASS
pause

:ERROR
rem color 4
.\py_scripts\ImageProgramming\Arbel_EVB_FlashProg.exe -open-desc "NPCM8mnx_Evaluation_Board B" -reset
echo.
echo.
echo ************************************** 
echo *** Flash Programming Failed  :-( ****
echo **************************************
echo.
echo.
timeout /T 100


:PASS
echo.
echo.
echo ************************************** 
echo *** Flash Programming Passed :-)  ****
echo **************************************
echo.
echo.
pause
exit


