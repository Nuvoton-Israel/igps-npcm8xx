@echo OFF

::: Note: 
:: * Make sure the following J2 header pins are populate with jumpers: 
::    > J2.3  & J2.4 : Port A.0; STRAP7 (BMC pins are at Hi-Z).  (** only on PCB version X01)
::    > J2.5  & J2.6 : Port A.1; STRAP2 (skip init or debug mode).  (** only on PCB version X01)
::    > J2.7  & J2.8 : Port A.2; STRAP5 (Rout BSP signals via Host SI2 pins). 
::    > J2.9  & J2.10: Port A.3; STRAP8 (Enable security mode to simulate secure path). 
::    > J2.11 & J2.12: Port A.4; VR_ENABLE_N (EVB Power ON / OFF). 
::    > J2.13 & J2.14: Port A.5; STRAP9 (Enable Flash UART upadte routine - FUP). 
::    > J2.15 & J2.16: Port A.6; PORST_N (Power-On-Reset). 
::    > J2.17 & J2.18: Port A.7; CORST_N (Core-Reset). 
:: * Make sure STRAP DIP-SWITCH are at OFF position. 
	
SET PIN_HIGH=1 1 
SET PIN_LOW=1 0
SET PIN_IN=0 0

SET STRAP7=0 
SET STRAP7_ASSERTED=-pin-set %STRAP7% %PIN_LOW%
SET STRAP7_RELEASE=-pin-set %STRAP7% %PIN_IN%

SET STRAP2=1
SET STRAP2_ASSERTED=-pin-set %STRAP2% %PIN_LOW%
SET STRAP2_RELEASE=-pin-set %STRAP2% %PIN_IN%

SET STRAP5=2
SET STRAP5_ASSERTED=-pin-set %STRAP5% %PIN_LOW%
SET STRAP5_RELEASE=-pin-set %STRAP5% %PIN_IN%

SET STRAP8=3
SET STRAP8_ASSERTED=-pin-set %STRAP8% %PIN_LOW%
SET STRAP8_RELEASE=-pin-set %STRAP8% %PIN_IN%

SET VR_ENABLE_N=4
SET POWER_OFF=-pin-set %VR_ENABLE_N% %PIN_HIGH%
SET POWER_ON=-pin-set %VR_ENABLE_N% %PIN_IN%

SET STRAP9=5
SET STRAP9_ASSERTED=-pin-set %STRAP9% %PIN_LOW%
SET STRAP9_RELEASE=-pin-set %STRAP9% %PIN_IN%

SET PORST_N=6
SET PORST_ASSERTED=-pin-set %PORST_N% %PIN_LOW%
SET PORST_RELEASE=-pin-set %PORST_N% %PIN_IN%

SET CORST_N=7
SET CORST_ASSERTED=-pin-set %CORST_N% %PIN_LOW%
SET CORST_RELEASE=-pin-set %CORST_N% %PIN_IN%

rem Arbel_EVB_Automation -help
rem Arbel_EVB_Automation -list


:: if one Arbel EVB is connected, -open-desc command can be use. 
Arbel_EVB_Automation -open-desc "NPCM8mnx_Evaluation_Board A" %PORST_ASSERTED% %STRAP5_ASSERTED% -update -delay 100 %PORST_RELEASE% -update -delay 100
echo Funtion returned: %ERRORLEVEL%

rem pause



