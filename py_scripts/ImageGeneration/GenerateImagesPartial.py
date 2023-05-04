# SPDX-License-Identifier: GPL-2.0
#
# Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
#
# Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
#-------------------------------------------------------------------------

import sys
import os
import shutil
import time

from shutil import copy
from shutil import move
from shutil import rmtree

from .BinarySignatureGenerator import *
from .GenerateKeyRSA import *
from .GenerateKeyECC import *
from .BinaryGenerator import *
from .CRC32_Generator import *
from .GenerateImages import *
from  .key_setting_edit_me import *


	
def ReplaceComponent(TypeOfKey, pinCode,isPalladium, component_num):

	currpath = os.getcwd()

	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	
	ticks = int(time.time()) % 0xFFFFFFFF

	try:
		if TypeOfKey == "HSM":
			if (os.path.isfile("pkcs11-tool.exe") == False):
				print("pkcs11-tool.exe doesn't exist!")
				return
		
		if (int(component_num) == 0):
			print("\n======\nTo replace: \n======\nKMT       press 1\nTIP_FW    press 2\nBootBlock press 3\nUboot     press 4\nCP        press 5\n"  \
			"Fuse file press 6\nBL31      press 7\nOpTee     press 8\nSkmt      press 9\nNO_TIP BB press 10\n")

		if (int(component_num) == 0):
			choice = eval(input("\n Please don't forget to step over the binary in the 'inputs' folder before running this script\n"))
		else:
			choice = int(component_num)
		
		print(("\n  Selected option is " + str(choice) + "\n\nCopying secured files to output_binaries..."))

		if choice != 1 and choice != 2 and choice != 3  and choice != 4 and choice != 5 and choice != 6 and choice != 7 and choice != 8 and choice != 9 and choice != 10:
			print("No such choice \n")
			return
		
		if (choice != 6):
			shutil.copy(KmtAndHeader_secure_bin                                       , KmtAndHeader_bin)
			shutil.copy(SkmtAndHeader_secure_bin                                      , SkmtAndHeader_bin)
			shutil.copy(TipFwAndHeader_L0_secure_bin                                  , TipFwAndHeader_L0_bin)
			shutil.copy(TipFwAndHeader_L1_secure_bin                                  , TipFwAndHeader_L1_bin)
			shutil.copy(BL31_AndHeader_secure_bin                                     , BL31_AndHeader_bin)
			shutil.copy(OpTeeAndHeader_secure_bin                                     , OpTeeAndHeader_bin)
			shutil.copy(UbootAndHeader_secure_bin                                     , UbootAndHeader_bin)
			shutil.copy(BootBlockAndHeader_secure_bin                                 , BootBlockAndHeader_bin)
			shutil.copy(BootBlockAndHeader_no_tip_secure_bin                          , BootBlockAndHeader_no_tip_bin)
			shutil.copy(CpAndHeader_secure_bin                                        , CpAndHeader_bin)
			shutil.copy(Kmt_TipFwL0_Skmt_TipFwL1_secure_bin                           , Kmt_TipFwL0_Skmt_TipFwL1_bin)
			shutil.copy(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_secure_bin, Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_bin)
			
		# Sign Images (and a secure  image) according to the choice
		if (choice == 1):
			print("Replace KMT")
			Replace_binary_single_byte(KmtAndHeader_bin,       140, ord(otp_key_which_signs_kmt[-1]) - ord('0'))
			Replace_binary_array(KmtAndHeader_bin,       0xBC, ticks, 4, True, "KMT       add timestamp")
			Generate_binary(KmtAndHeader_xml      , KmtAndHeader_bin)
			CRC32_binary(KmtAndHeader_bin        , 112    , 12     , KmtAndHeader_bin)
			Sign_binary(KmtAndHeader_bin,       112, eval(otp_key_which_signs_kmt),       16, KmtAndHeader_secure_bin,       TypeOfKey, pinCode, eval("id_otp_key" + otp_key_which_signs_kmt[-1]))
			shutil.copy(KmtAndHeader_secure_bin,            KmtAndHeader_bin)
			
		elif (choice == 2):
			print("Replace TIP_FW")
			Pad_bin_file_inplace(  Tip_FW_L0_file ,  32)
			Pad_bin_file_inplace(  Tip_FW_L1_file ,  32)
			Generate_binary(TipFwAndHeader_L0_xml    , TipFwAndHeader_L0_bin)
			Generate_binary(TipFwAndHeader_L1_xml    , TipFwAndHeader_L1_bin)
			Replace_binary_single_byte(TipFwAndHeader_L0_bin,  140, ord(kmt_key_which_signs_tip_fw_L0[-1]) - ord('0'))
			Replace_binary_single_byte(TipFwAndHeader_L1_bin,  140, ord(skmt_key_which_signs_tip_fw_L1[-1]) - ord('0'))
			Replace_binary_array(TipFwAndHeader_L0_bin,  0xBC, ticks, 4, True, "L0        add timestamp")
			Replace_binary_array(TipFwAndHeader_L1_bin,  0xBC, ticks, 4, True, "L1        add timestamp")
			CRC32_binary(TipFwAndHeader_L0_bin      , 112    , 12     , TipFwAndHeader_L0_bin)
			CRC32_binary(TipFwAndHeader_L1_bin      , 112    , 12     , TipFwAndHeader_L1_bin)
			Sign_binary(TipFwAndHeader_L0_bin,  112, eval(kmt_key_which_signs_tip_fw_L0),  16, TipFwAndHeader_L0_secure_bin,  TypeOfKey, pinCode, eval("id_kmt_key" + kmt_key_which_signs_tip_fw_L0[-1]))
			Sign_binary(TipFwAndHeader_L1_bin,  112, eval(skmt_key_which_signs_tip_fw_L1), 16, TipFwAndHeader_L1_secure_bin,  TypeOfKey, pinCode, eval("id_skmt_key" + skmt_key_which_signs_tip_fw_L1[-1]))
			shutil.copy(TipFwAndHeader_L0_secure_bin,            TipFwAndHeader_L0_bin)
			shutil.copy(TipFwAndHeader_L1_secure_bin,            TipFwAndHeader_L1_bin)
			
		elif (choice == 3):
			print("Replace bootblock")
			Pad_bin_file_inplace(  bb_bin         ,  32)
			Generate_binary(BootBlockAndHeader_xml, BootBlockAndHeader_bin)
			Replace_binary_single_byte(BootBlockAndHeader_bin, 140, ord(skmt_key_which_signs_bootblock[-1]) - ord('0'))
			Replace_binary_array(BootBlockAndHeader_bin, 0xBC, ticks, 4, True, "Bootblock add timestamp")
			Sign_binary(BootBlockAndHeader_bin, 112, eval(skmt_key_which_signs_bootblock), 16, BootBlockAndHeader_secure_bin, TypeOfKey, pinCode, eval("id_skmt_key" + skmt_key_which_signs_bootblock[-1]))
			shutil.copy(BootBlockAndHeader_secure_bin,            BootBlockAndHeader_bin)
			
		elif (choice == 10):
			print("Replace bootblock no tip")
			Pad_bin_file_inplace(  bb_bin_no_tip         ,  32)
			Generate_binary(BootBlockAndHeader_no_tip_xml, BootBlockAndHeader_bin)
			Replace_binary_array(BootBlockAndHeader_no_tip_bin, 0xBC, ticks, 4, True, "Bootblock add timestamp")
			shutil.copy(BootBlockAndHeader_no_tip_secure_bin,            BootBlockAndHeader_no_tip_bin)
		
		elif (choice == 4):
			print("Replace uboot")
			Pad_bin_file_inplace(  uboot_bin      ,  32)
			Generate_binary(UbootAndHeader_xml    , UbootAndHeader_bin)
			Replace_binary_single_byte(UbootAndHeader_bin,     140, ord(skmt_key_which_signs_uboot[-1]) - ord('0'))
			Replace_binary_array(UbootAndHeader_bin,     0xBC, ticks, 4, True, "UBOOT     add timestamp")
			Uboot_header_embed_pointers_to_all_fw()
			Sign_binary(UbootAndHeader_bin,     112, eval(skmt_key_which_signs_uboot),     16, UbootAndHeader_secure_bin,     TypeOfKey, pinCode, eval("id_skmt_key" + skmt_key_which_signs_uboot[-1]))
			shutil.copy(UbootAndHeader_secure_bin,            UbootAndHeader_bin)
			
		elif (choice == 5):
			print("Replace CP")
			Generate_binary(CpAndHeader_xml       , CpAndHeader_bin)
			
		elif (choice == 6):
			print("Replace OTP image")
			Generate_binary(arbel_fuse_map_xml    , arbel_fuse_map_bin)
			
		elif (choice == 7):
			print("Replace BL31")
			Pad_bin_file_inplace(  bl31_bin       ,  32)
			Generate_binary(BL31_AndHeader_xml    , BL31_AndHeader_bin)
			Replace_binary_single_byte(BL31_AndHeader_bin,     140, ord(skmt_key_which_signs_BL31[-1]) - ord('0'))
			Replace_binary_array(BL31_AndHeader_bin,     0xBC, ticks, 4, True, "BL31      add timestamp")
			Sign_binary(BL31_AndHeader_bin,     112, eval(skmt_key_which_signs_BL31),      16, BL31_AndHeader_secure_bin,     TypeOfKey, pinCode, eval("id_skmt_key" + skmt_key_which_signs_BL31[-1]))
			shutil.copy(BL31_AndHeader_secure_bin,            BL31_AndHeader_bin)
			
		elif (choice == 8):
			print("Replace TEE")
			Pad_bin_file_inplace(  tee_bin        ,  32)
			Generate_binary(OpTeeAndHeader_xml    , OpTeeAndHeader_bin)
			Replace_binary_single_byte(OpTeeAndHeader_bin,     140, ord(skmt_key_which_signs_OpTee[-1]) - ord('0'))
			Replace_binary_array(OpTeeAndHeader_bin,     0xBC, ticks, 4, True, "OpTee     add timestamp")
			Sign_binary(OpTeeAndHeader_bin,     112, eval(skmt_key_which_signs_OpTee),     16, OpTeeAndHeader_secure_bin,     TypeOfKey, pinCode, eval("id_skmt_key" + skmt_key_which_signs_OpTee[-1]))
			shutil.copy(OpTeeAndHeader_secure_bin,            OpTeeAndHeader_bin)
			
		elif (choice == 9):
			print("Replace SKMT")
			Replace_binary_single_byte(SkmtAndHeader_bin,       140, ord(kmt_key_which_signs_skmt[-1]) - ord('0'))
			Replace_binary_array(SkmtAndHeader_bin,      0xBC, ticks, 4, True, "SKMT      add timestamp")
			Generate_binary(SkmtAndHeader_xml      , SkmtAndHeader_bin)
			CRC32_binary(SkmtAndHeader_bin        , 112    , 12     , SkmtAndHeader_bin)
			Sign_binary(SkmtAndHeader_bin,       112, eval(kmt_key_which_signs_skmt),       16, SkmtAndHeader_secure_bin,       TypeOfKey, pinCode, eval("id_skmt_key" + kmt_key_which_signs_skmt[-1]))
			shutil.copy(SkmtAndHeader_secure_bin,            SkmtAndHeader_bin)
			
		if (choice != 6):
			MergeBinFilesAndPadAndPrint(isPalladium)
		
		# Copy new images to Secure Directory
		if (choice != 6):
			MoveToFolder(isPalladium, secure_outputs_dir)

	except (Exception) as e:
		print(("\n GenerateImages.py: Error building binaries (%s)" % str(e)))
		raise

	finally:
		os.chdir(currpath)
