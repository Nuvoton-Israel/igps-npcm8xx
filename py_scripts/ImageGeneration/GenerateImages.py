# SPDX-License-Identifier: GPL-2.0
#
# Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
#
# Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
#-------------------------------------------------------------------------

import sys
import os
import time
import glob

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

def Run(TypeOfKey, pinCode, isPalladium, useSignedCombo0, isDebug, remotehsm_embed=False):
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
		
		# In RemoteHSM embed mode, backup signature files before Run_Init() deletes them
		if TypeOfKey == "RemoteHSM" and remotehsm_embed:
			import shutil
			import tempfile
			temp_sig_dir = tempfile.mkdtemp(prefix="remotehsm_sigs_")
			sig_files = []
			sig_pattern = os.path.join(outputs_dir, "*_sig.*")
			existing_sigs = glob.glob(sig_pattern)
			if existing_sigs:
				for sig_file in existing_sigs:
					backup_path = os.path.join(temp_sig_dir, os.path.basename(sig_file))
					shutil.copy2(sig_file, backup_path)
					sig_files.append((sig_file, backup_path))
			else:
				print("\033[91m" + "ERROR: RemoteHSM embed mode but no signature files found!" + "\033[0m")
				print("Expected signature files in: " + outputs_dir)
				return
		
		Run_Init()
		
		# Restore signature files after Run_Init()
		if TypeOfKey == "RemoteHSM" and remotehsm_embed:
			import shutil
			for orig_path, backup_path in sig_files:
				shutil.copy2(backup_path, orig_path)
			# Clean up temp directory
			shutil.rmtree(temp_sig_dir, ignore_errors=True)

		Hardening_all_images()

		Generate_Or_Load_Keys(TypeOfKey, TypeOfKey_TIP, TypeOfKey_BMC, pinCode)
		
		Build_basic_images(TypeOfKey)
		
		# for debug cases, don't edit the values and leave them as were on XMLs 
		if isDebug is False:
			Write_key_ind_and_key_mask_to_headers()	
			Write_LMS_flags_to_headers()
			Write_timestamp_and_IV_to_headers()

		Uboot_header_embed_pointers_to_all_fw()
        
		Write_CRC_to_TIP_images()
		
		MergeBinFilesAndPadAndPrint(isPalladium)
		
		# Move Basic images to Basic Directory
		MoveToFolder(isPalladium, basic_outputs_dir)

		if TypeOfKey == "RemoteHSM":
			if remotehsm_embed:
				# Second run: embed provided signatures
				# NOTE: Sign_combo0/1 with RemoteHSM mode calls Embed_external_sig(), NOT Sign_binary()
				print("\033[95m" + "==========================================================")
				print("== RemoteHSM: Embedding signatures...")
				print("==========================================================" + "\033[0m")
				Sign_combo0(TypeOfKey, pinCode, isPalladium, TypeOfKey_TIP, TypeOfKey_BMC,)
				Sign_combo1(TypeOfKey, pinCode, isPalladium, TypeOfKey_TIP, TypeOfKey_BMC)
			else:
				# First run: extract binaries for signing
				print("\033[95m" + "==========================================================")
				print("== RemoteHSM: Extracting binaries for external signing...")
				print("==========================================================" + "\033[0m")
				extract_bin_file_to_sign(KmtAndHeader_basic_bin      , 112)
				extract_bin_file_to_sign(TipFwAndHeader_L0_basic_bin , 112)
				extract_bin_file_to_sign(SA_TipFwAndHeader_L0_basic_bin,112)
				extract_bin_file_to_sign(SkmtAndHeader_basic_bin     , 112)
				extract_bin_file_to_sign(TipFwAndHeader_L1_basic_bin , 112)
				extract_bin_file_to_sign(BootBlockAndHeader_basic_bin, 112)
				extract_bin_file_to_sign(BL31_AndHeader_basic_bin    , 112)
				extract_bin_file_to_sign(OpTeeAndHeader_basic_bin    , 112)
				extract_bin_file_to_sign(UbootAndHeader_basic_bin    , 112)
				print("\033[92m" + "==========================================================")
				print("== Extraction complete. Sign the files and run again with 'embed'.")
				print("===========================================================" + "\033[0m")
				# Clean up - remove all non-extraction files from Basic/ folder
				for f in glob.glob(os.path.join(basic_outputs_dir, "*.bin")):
					if "_part_to_sign" not in f:
						os.remove(f)
				# Skip merging on first run - no signatures yet
				return

		else: # all other typeofkey continue to signing
			Sign_combo0(TypeOfKey, pinCode, isPalladium, TypeOfKey_TIP, TypeOfKey_BMC,)
			Sign_combo1(TypeOfKey, pinCode, isPalladium, TypeOfKey_TIP, TypeOfKey_BMC)
			
		Merge_signed_files(isPalladium, useSignedCombo0)

	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print("\n GenerateImages.py: Error building binaries (%s)" % str(e))
		raise

	finally:
		os.chdir(currpath)
