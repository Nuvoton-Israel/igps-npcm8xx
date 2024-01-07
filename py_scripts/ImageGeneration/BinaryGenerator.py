# SPDX-License-Identifier: GPL-2.0
#
# Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
#
# Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
#-------------------------------------------------------------------------

import sys
import os
import io


bingo = "bingo"
linux_prefix = " ./"


class BingoError(Exception):

	def __init__(self, value):
		self.strerror = "Bingo error value:" + str(value)
	def __str__(self):
		return repr(self.strerror)
		
		
def Pad_bin_file_inplace(inF, align):
	padding_size = 0
	padding_size_end = 0
	
	F_size = os.path.getsize(inF)
	
	if ((F_size % align) == 0):
		return 0

	padding_size = align - (F_size % align)
		
	print(("\033[95m" + "Pad file in place " + inF ))
	print(("Size before " + hex(F_size) + " bytes"))
	
	infile = open(inF, "ab")
	infile.seek(0, 2)
	infile.write(b'\x00' * padding_size)
	infile.close()
	
	print(("Size after " + hex(os.path.getsize(inF)) + " bytes"))

	return padding_size


# merge inF1 and inF2 to create outF. 
# Align both files according to align size. pad with 0xFF
def Merge_bin_files_and_pad(inF1, inF2, outF, align, padding_at_end, align_end = 0x1000):

	padding_size = 0
	padding_size_end = 0
	
	status = 0
	
	print(("\t\033[95m" + "Merge " + inF1 + " + " + inF2 + " => " + outF + "\033[97m"))
	
	if (os.path.isfile(inF1) == False):
		print(("currpath " +  os.getcwd()))
		print(("\033[91m" + "Merge_bin_files_and_pad   Error: " +  inF1 + " file 1 is missing\n\n" + "\033[97m"))
		status = -1
		
	if (os.path.isfile(inF2) == False):
		print(("currpath " +  os.getcwd()))
		print(("\033[91m" + "Merge_bin_files_and_pad   Error: " + inF2 + " file 2 is missing\n\n" + "\033[97m"))
		status  = -1
		
	if (status != 0):
		return status
	
	F1_size = os.path.getsize(inF1)
	F2_size = os.path.getsize(inF2)

	
	if ((F1_size % align) != 0):
		padding_size = align - (F1_size % align)
	
	if ((F2_size % align_end) != 0):
		padding_size_end = align_end - (F2_size % align_end)
		
	
	print(("\tMerge " + hex(F1_size) + " bytes + " + hex(F2_size) + " bytes => " + outF))
	print(("\tpadding middle " + hex(padding_size) + "\tpadding end " + hex(padding_size_end) + "\n\n" + "\x1b[0m"))
	
	startLoc = F1_size + padding_size

	with open(outF, "wb") as file3:
		with open(inF1, "rb") as file1:
			data = file1.read()
			file3.write(data)

		file3.write(b'\xFF' * padding_size)

		with open(inF2, "rb") as file2:
			data = file2.read()
			file3.write(data)

		file3.write(b'\xFF' * padding_size_end)

	file1.close()
	file2.close()
	file3.close()
	return startLoc

# covert bin to hex file format, same way Palladium likes its files. 
def Convert_file_to_hex_like_PD_likes_it(inF, outF, bytes_in_line):
	
	print(("\033[95m" + "Convert to hex " + inF + " => " + outF))
	
	with open(outF, "w") as file2:
		with open(inF, "rb") as file1:
			for x in range(os.path.getsize(inF)):
				data = file1.read(bytes_in_line)
				if ord(data) < 16:
					file2.write(str('0'))
				if ord(data) == 0:
					file2.write(str('0'))
				file2.write(hex(ord(data)).lstrip("0x"))
				file2.write('\n')
	file1.close()
	file2.close()


def Generate_binary(xmlFile, outputFile, mask = False):

	_bingo = bingo
	if os.name != "nt":
		_bingo = linux_prefix + bingo
	
	print(("\033[95m" + "=========================================================="))
	print(("== call bingo Generating %s  using %s    " % (outputFile, xmlFile)))
	print(("==========================================================" + "\x1b[0m"))
	if (mask == True):
		cmd = "%s -mask \"%s\" -o \"%s\" " % (_bingo, xmlFile, outputFile)
	else:
		cmd = "%s \"%s\" -o \"%s\" " % (_bingo, xmlFile, outputFile)

	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	try:
		print(cmd)
		rc = os.system(cmd)
		os.chdir(currpath)
		if rc != 0:
			raise BingoError(rc)
	except:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print(("BinaryGenerator.py: generating %s failed" % (outputFile)))
		print((" error in  %s " % (xmlFile)))
		raise
	finally:
		os.chdir(currpath)
