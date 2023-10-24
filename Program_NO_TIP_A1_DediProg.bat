rem  SPDX-License-Identifier: GPL-2.0
rem 
rem  Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
rem 
rem  Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
rem -------------------------------------------------------------------------



"C:\Program Files (x86)\DediProg\SF100\dpcmd.exe" -u .\py_scripts\ImageGeneration\output_binaries\Basic\image_no_tip.bin    --type W25Q256JV
"C:\Program Files (x86)\DediProg\SF100\dpcmd.exe" -u .\py_scripts\ImageGeneration\output_binaries\Secure\SA_Kmt_TipFwL0.bin --type W25Q256JV --addr 0x200000

