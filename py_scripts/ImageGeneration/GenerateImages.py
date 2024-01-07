# SPDX-License-Identifier: GPL-2.0
#
# Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
#
# Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
#-------------------------------------------------------------------------

import sys
import os
import time

from shutil import copy
from shutil import move
from shutil import rmtree

from .BinarySignatureGenerator import *
from .GenerateKeyECC import *
from .GenerateKeyRSA import *
from .BinaryGenerator import *
from .CRC32_Generator import *

from .IGPS_files import *
from .IGPS_common import *
from .Register_csv_parse import *


def Run(TypeOfKey, pinCode,isPalladium):
	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	
	# in case user wants to use HSM only TIP side images will be signed with HSM. The other images are build with yocto+openssl
	TypeOfKey_TIP = "HSM"
	TypeOfKey_BMC = "openssl"
	try:
		if TypeOfKey == "HSM":
			if (os.path.isfile("pkcs11-tool.exe") == False):
				print("pkcs11-tool.exe doesn't exist!")
				return
		# openssl: use openssl for both images
		else:
			TypeOfKey_TIP = TypeOfKey
			TypeOfKey_BMC = TypeOfKey
		
		Run_Init()

		Hardening_all_images()

		Generate_Or_Load_Keys(TypeOfKey, TypeOfKey_TIP, TypeOfKey_BMC, pinCode)
		
		Build_basic_images()
		
		Write_key_ind_and_key_mask_to_headers()

		Write_timestamp_and_IV_to_headers()

		Uboot_header_embed_pointers_to_all_fw()
		
		MergeBinFilesAndPadAndPrint(isPalladium)
		
		# Move Basic images to Basic Directory
		MoveToFolder(isPalladium, basic_outputs_dir)

		if TypeOfKey == "RemoteHSM":
			# For signing with an remote HSM extract binaries that need to be signed
			extract_bin_file_to_sign(KmtAndHeader_basic_bin      , 112)
			extract_bin_file_to_sign(TipFwAndHeader_L0_basic_bin , 112)
			extract_bin_file_to_sign(SA_TipFwAndHeader_L0_basic_bin,112)
			extract_bin_file_to_sign(SkmtAndHeader_basic_bin     , 112)
			extract_bin_file_to_sign(TipFwAndHeader_L1_basic_bin , 112)
			extract_bin_file_to_sign(BootBlockAndHeader_basic_bin, 112)
			extract_bin_file_to_sign(BL31_AndHeader_basic_bin    , 112)
			extract_bin_file_to_sign(OpTeeAndHeader_basic_bin    , 112)
			extract_bin_file_to_sign(UbootAndHeader_basic_bin    , 112)

		else: # all other typeofkey continue to signing
			Sign_combo0(TypeOfKey, pinCode, isPalladium, TypeOfKey_TIP, TypeOfKey_BMC)
			Sign_combo1(TypeOfKey, pinCode, isPalladium, TypeOfKey_TIP, TypeOfKey_BMC)
			
		Merge_signed_files(isPalladium)

	except (Exception) as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print("\n GenerateImages.py: Error building binaries (%s)" % str(e))
		raise

	finally:
		os.chdir(currpath)

