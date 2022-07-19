# SPDX-License-Identifier: GPL-2.0
#
# Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
#
# Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
#-------------------------------------------------------------------------

import sys
import os
import binascii
from struct import *


def crc32_tab_val( c ):
	crc = int(c)  % (1<<32)
	for x in range(0, 8):
		if ( crc & 0x00000001 ):
				crc = ( (crc >> 1)  % (1<<32) ) ^ 0xEDB88320
		else:
				crc =   crc >> 1
		crc = crc  % (1<<32)
	return crc
		
def update_crc( crc, c ):

    long_c = int(0x000000ff & c)   % (1<<32)
    tmp = (crc ^ long_c)    % (1<<32)
    crc = ((crc >> 8) ^ crc32_tab_val( tmp & 0xff ))   % (1<<32)
    crc = crc  % (1<<32)
    return crc;


	    
def CalcCRC32(bin_filename, begin_offset, embed_ecc, output_filename, zero_crc):

	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	try:

		# calc CRC, convert from int to unsigned int
		input_size = bytearray(os.path.getsize(bin_filename))
		
		if (begin_offset >= input_size.__len__()):
			print("\nCRC32_Generator.py : file too small\n")

		crc = 0
		if (zero_crc == False):
			with open(bin_filename, "rb") as binary_file:
				## Read first begin_offset bytes of data
				tmp = binary_file.read(begin_offset)
				
				while True:
					va = binary_file.read(1)
					if not va:
						break
					# Note: from some unknown reason, 
					# the following does not work OK.
					# using an internal function instead.
					# crc = binascii.crc32(bytearray(ord(va)), crc)
					
					crc = update_crc(crc, ord(va))

			crc = crc  & 0xffffffff
			print(("\n\nwrite to output file " + output_filename + " CRC32: " + str(hex(crc))))

		with open(bin_filename, "rb") as binary_file:
			input = binary_file.read()
			
		crc_arr = bytearray(4)
		for ind in range(4):
			crc_arr[ind] = (crc >> (ind*8) ) & 255
			print((hex(crc_arr[ind])))
		# py3 in above: crc.to_bytes(32, sys.byteorder)
		
		#embed CRC in image
		output = input[:embed_ecc] + crc_arr + input[(embed_ecc + 4):]


		# write the input with the embedded CRC to the output file
		output_file = open(output_filename, "w+b")
		output_file.write(output)
		output_file.close()
		
		print(("write to output file " + output_filename + " CRC32: " + str(hex(crc)) + " done"))

	except:
		print(("\n\n py_scripts\\ImageGeneration\\CRC32_Generator.py: add crc32 %s failed" % (output_filename)))
		raise
	finally:
		os.chdir(currpath)


def CRC32_binary(binfile, begin_offset, embed_ecc, outputFile):	
	print(("\033[93m" + "=========================================================="))
	print(("== Get CRC32 %s " % (binfile)))
	print(("==========================================================" + "\x1b[0m"))
	CalcCRC32(binfile, begin_offset, embed_ecc, outputFile, False)

def CRC32_remove(binfile, begin_offset, embed_ecc, outputFile):	
	print(("\033[93m" + "=========================================================="))
	print(("== Remove CRC32 %s " % (binfile)))
	print(("==========================================================" + "\x1b[0m"))
	CalcCRC32(binfile, begin_offset, embed_ecc, outputFile, True)
