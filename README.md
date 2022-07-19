# IGPS
Image Generation And Programming Scripts for Arbel BMC

## How to use
IGPS is written for Python 3.7

Make sure you have it installed and added to your %PATH%.

In addition, please download and compile the following tools:
(a precompiled version for Windows users is already part of this repo)

### 1.	Bingo
https://github.com/Nuvoton-Israel/bingo
Bingo is a generic tool that can build any header. 
The Header format and contents are defined on an external xml file.
There is nothing Arbel specific on the tool itself (Same Bingo can be used in Poleg)
More details and a basic set of examples are available on the link above.

### 2.	OpenSSL
Version: OpenSSL 1.0.2j-fips  26 Sep 2016
Linux users can download it from:
https://www.openssl.org/source/

### 3.	UUT
https://github.com/Nuvoton-Israel/uart-update-tool
Used for programing the flash using the Arbel ROM UFPP mode.

Download and compile these three tools. The first tools should be placed inside ./ImageGeneration
The last tool should be placed inside ./ImageProgramming.

WARNING: Programming with UUT is only supported in  NPCM8XX Z1. Tool is obsulete.

## Notes about input files
All the files in this package are used for EB\SVB. For other vendors, please contact tali.perry@nuvoton.com. 

## How to use:

### Image generation:
```
python ./UpdateInputsBinaries_%Chip*_%Board%.py
python ./GenerateAll.py
```
Chip:  A1\Z1 device.
Board: SVB\EB are currently supported. 

Note: UpdateInputBinaries*.bat resets all the images and xml files inside py_scripts\ImageGeneration\inputs folder.
After that users can override the existing files in inputs folder, or use as is.
For a signed release there is also an option to use ReplaceComponent.bat to replace a single file inside a
signed image.

### Signed version of IGPS
Nuvoton provides to customers locked devices.
To use those devices Nuvoton use its own private key to sign the images.
This means users can generate flash images for these devices.
Nuvoton provides a pre-signed IGPS version for locked devices.
Update* and Generate* are not possible, only programming.
If user wishes to update uboot\bl31\bootblock they may still do so by replaceing the file in inputs folder and executing ReplaceComponent.bat

### Image programming:
Connect a serial port (via COM port or USB to Serial) to Serial Interface 2
Set strap9 to active low and issue power-on reset
```
python ./Program%File%_%Security%_%Tool%.py
```

File: 

	All: All FWs except Linux: KMT, TFT, bootblock, BL31, OpTee, uboot. (most common use case).
	Bootblock: All FW up to bootblock (KMT, TFT, bootblock)
	1FF: One File Flash: all FW, including Linux. Require 32MB flash or higher.
Security: 

	Basic (none-secure device)
	Secure (locked device)
Tool: can be 

	EVB: support blue\green EVB board only. Require automation jumpers. Windows only
	DediProg: SVB has a headaer for external Flash Programmer DediProg.
	FUP: using internal UART of the Arbel. This feature is only supported in Z1. Deprecated.


For EVB and FUP: Disable all terminal apps before execution.
