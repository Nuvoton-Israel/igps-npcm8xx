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
import json
# Define the correct path to the JSON file
json_file_path = os.path.join(os.path.dirname(__file__), 'key_setting_edit_me.json')
# Load the JSON configuration
with open(json_file_path, 'r') as file:
	config = json.load(file)
# Use the configuration values
lms_flags                          = config.get("lms_flags", {})
isECC                              = config.get("isECC")
isLMS                              = any(lms_flags.values())
isRemoteHSM                        = config.get("isRemoteHSM", False)
COMBO1_OFFSET                      = config.get("COMBO1_OFFSET")
otp_key_which_signs_kmt            = config["otp_key_which_signs_kmt"]
kmt_key_which_signs_tip_fw_L0      = config["kmt_key_which_signs_tip_fw_L0"]
kmt_key_which_signs_skmt           = config["kmt_key_which_signs_skmt"]
skmt_key_which_signs_tip_fw_L1     = config["skmt_key_which_signs_tip_fw_L1"]
skmt_key_which_signs_bootblock     = config["skmt_key_which_signs_bootblock"]
skmt_key_which_signs_BL31          = config["skmt_key_which_signs_BL31"]
skmt_key_which_signs_OpTee         = config["skmt_key_which_signs_OpTee"]
skmt_key_which_signs_uboot         = config["skmt_key_which_signs_uboot"]
lms_key_which_signs_kmt            = config["lms_key_which_signs_kmt"]
lms_key_which_signs_tip_fw_L0      = config["lms_key_which_signs_tip_fw_L0"]
lms_key_which_signs_skmt           = config["lms_key_which_signs_skmt"]
lms_key_which_signs_tip_fw_L1      = config["lms_key_which_signs_tip_fw_L1"]
lms_key_which_signs_bootblock      = config["lms_key_which_signs_bootblock"]
lms_key_which_signs_BL31           = config["lms_key_which_signs_BL31"]
lms_key_which_signs_OpTee          = config["lms_key_which_signs_OpTee"]
lms_key_which_signs_uboot          = config["lms_key_which_signs_uboot"]


if isLMS and not isRemoteHSM:
	from .GenerateKeyLMS import *
from .BinaryGenerator import *
from .CRC32_Generator import *

from .IGPS_files import *
from .Register_csv_parse import *

kmtS          =   0xFFFFFFFF
tipS_L0       =   0xFFFFFFFF
saTipS_L0     =   0xFFFFFFFF
skmtS         =   0xFFFFFFFF
tipS_L1       =   0xFFFFFFFF
bbS           =   COMBO1_OFFSET
bl31S         =   0xFFFFFFFF
OpTeeS        =   0xFFFFFFFF
ubootS        =   0xFFFFFFFF
cpS           =   0xFFFFFFFF
imageS        =   0xFFFFFFFF
romfsS        =   0xFFFFFFFF
dtbS          =   0xFFFFFFFF

kmtS_size      =   0xFFFFFFFF
tipS_L0_size   =   0xFFFFFFFF
satipS_L0_size =   0xFFFFFFFF
skmtS_size  =    0xFFFFFFFF
tipS_L1_size   =   0xFFFFFFFF
bbS_size       =   0xFFFFFFFF
bl31S_size     =   0xFFFFFFFF
OpTeeS_size    =   0xFFFFFFFF
ubootS_size    =   0xFFFFFFFF
cpS_size       =   0xFFFFFFFF
imageS_size    =   0xFFFFFFFF
romfsS_size    =   0xFFFFFFFF
dtbS_size      =   0xFFFFFFFF





def Run_Init():
	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	try:
		if os.path.isdir(outputs_dir):
			rmtree(outputs_dir)
		os.mkdir(outputs_dir)
		os.mkdir(basic_outputs_dir)
		os.mkdir(secure_outputs_dir)
		os.mkdir(registers_outputs_dir)
		os.mkdir(tmp_outputs_dir)
		
	except (Exception) as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print(("\n GenerateImages.Run_Init.py: Error Create output folder (%s)" % str(e)))
		raise

	finally:
		os.chdir(currpath)

def allign_to_sector(num, round_to):
	if (num % round_to == 0):
		return num
	else:
		return  num + round_to - (num % round_to)
	

def Uboot_header_embed_pointers_to_all_fw():
		# add image pointers to uboot header
		
		# calc sizes of images + headers:
		kmtS_size =      os.path.getsize(KmtAndHeader_bin)
		tipS_L0_size =   os.path.getsize(TipFwAndHeader_L0_bin)
		skmtS_size  =    os.path.getsize(SkmtAndHeader_bin)
		tipS_L1_size =   os.path.getsize(TipFwAndHeader_L1_bin)
		bbS_size =       os.path.getsize(BootBlockAndHeader_bin)
		bbS_no_tip_size = os.path.getsize(BootBlockAndHeader_no_tip_bin)
		bl31S_size  =    os.path.getsize(BL31_AndHeader_bin)
		OpTeeS_size =    os.path.getsize(OpTeeAndHeader_bin)
		ubootS_size =    os.path.getsize(UbootAndHeader_bin)
		imageS_size =    os.path.getsize(image_bin)
		romfsS_size =    os.path.getsize(romfs_bin)
		dtbS_size =      os.path.getsize(dtb_bin)
		
		
		bbS =  COMBO1_OFFSET
		bl31S  = bbS +    allign_to_sector(bbS_size    , 0x1000)
		OpTeeS = bl31S +  allign_to_sector(bl31S_size  , 0x1000)
		ubootS = OpTeeS + allign_to_sector(OpTeeS_size , 0x1000)
		imageS = ubootS + allign_to_sector(ubootS_size , 0x110000)
		romfsS = imageS + allign_to_sector(imageS_size , 0x1000)
		dtbS =   romfsS + allign_to_sector(romfsS_size , 0x1000)
		
		tip_total_size = kmtS_size + tipS_L0_size + skmtS_size + tipS_L1_size
		Replace_binary_array(UbootAndHeader_bin, 0x1B8, 0             , 4, True, "TIP base address")
		Replace_binary_array(UbootAndHeader_bin, 0x1BC, tip_total_size, 4, True, "TIP base size")
		
		Replace_binary_array(UbootAndHeader_bin, 0x1C0, bbS           , 4, True, "Bootblock base address")
		Replace_binary_array(UbootAndHeader_bin, 0x1C4, bbS_size      , 4, True, "Bootblock base size")
		
		Replace_binary_array(UbootAndHeader_bin, 0x1C8, bl31S         , 4, True, "BL31 base address")
		Replace_binary_array(UbootAndHeader_bin, 0x1CC, bl31S_size    , 4, True, "BL31 base size")
		
		Replace_binary_array(UbootAndHeader_bin, 0x1D0, OpTeeS        , 4, True, "OpTee base address")
		Replace_binary_array(UbootAndHeader_bin, 0x1D4, OpTeeS_size   , 4, True, "OpTee base size")
		
		Replace_binary_array(UbootAndHeader_bin, 0x1D8, ubootS        , 4, True, "uboot base address")
		Replace_binary_array(UbootAndHeader_bin, 0x1DC, ubootS_size   , 4, True, "uboot base size")
		
		Replace_binary_array(UbootAndHeader_bin, 0x1E0, imageS        , 4, True, "Linux base address")
		Replace_binary_array(UbootAndHeader_bin, 0x1E4, imageS_size   , 4, True, "Linux base size")
		
		Replace_binary_array(UbootAndHeader_bin, 0x1E8, dtbS          , 4, True, "Linux DTS base address")
		Replace_binary_array(UbootAndHeader_bin, 0x1EC, dtbS_size     , 4, True, "Linux DTS base size")
		
		Replace_binary_array(UbootAndHeader_bin, 0x1F0, romfsS        , 4, True, "Linux FS base address")
		Replace_binary_array(UbootAndHeader_bin, 0x1F4, romfsS_size   , 4, True, "Linux FS base size")


		# Replace_binary_array(UbootAndHeader_bin, 0x1BC, [0xAA, 0xBB, 0xCC, 0xDD], 4, False)


def MergeBinFilesAndPadAndPrint(isPalladium, useSignedCombo0: str = None):
	# Merge files
	bbS = COMBO1_OFFSET
	
	if useSignedCombo0 is None:
		tipS_L0 =      Merge_bin_files_and_pad(KmtAndHeader_bin            , TipFwAndHeader_L0_bin    , Kmt_TipFwL0_bin                       , 0x1000, 0x20)
		sa_tipS_L0 =   Merge_bin_files_and_pad(KmtAndHeader_bin            , SA_TipFwAndHeader_L0_bin , SA_Kmt_TipFwL0_bin                    , 0x1000, 0x20)
		tipS_L0_UT =   Merge_bin_files_and_pad(KmtAndHeader_bin            , TipFwAndHeader_L0_UT_bin , Kmt_TipFwL0_UT_bin                    , 0x1000, 0x20)
		skmtS  =       Merge_bin_files_and_pad(Kmt_TipFwL0_bin             , SkmtAndHeader_bin        , Kmt_TipFwL0_Skmt_bin                  , 0x1000, 0x20)
		tipS_L1 =      Merge_bin_files_and_pad(Kmt_TipFwL0_Skmt_bin        , TipFwAndHeader_L1_bin    , Kmt_TipFwL0_Skmt_TipFwL1_bin          , 0x1000, 0x20)
	else:
		# Use a pre-signed image from TIP_FW repository, include SA TIP and normal TIP FW:
		signed_TIP = os.path.join(useSignedCombo0, "Kmt_TipFwL0_Skmt_TipFwL1.bin")
		signed_SA_TIP = os.path.join(useSignedCombo0, "SA_Kmt_TipFwL0.bin")
		try:
			print(f"Copying signed combo0 {signed_TIP} to {Kmt_TipFwL0_Skmt_TipFwL1_bin}")
			copyfile(signed_TIP, Kmt_TipFwL0_Skmt_TipFwL1_bin)
			print(f"Copying signed combo0 {signed_SA_TIP} to {SA_Kmt_TipFwL0_bin}")
			copyfile(signed_SA_TIP, SA_Kmt_TipFwL0_bin)
		except Exception as e:
			print(f"current path: {os.getcwd()}")
			print("Failed to copy file: ", e)
			raise
		tipS_L0 = 0
		skmtS = 0
		tipS_L1 = 0

	bbS =       Merge_bin_files_and_pad(Kmt_TipFwL0_Skmt_TipFwL1_bin, BootBlockAndHeader_bin   , Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_bin, bbS   , 0x20)

	# check that bootblock is still at 512KB offset
	if (bbS != COMBO1_OFFSET):
		print("       =============   ERROR: TIP_FW overflow ======================")

	bl31S  =    Merge_bin_files_and_pad(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_bin                        , BL31_AndHeader_bin, Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_bin                                , 0x1000     , 0x20)
	OpTeeS =    Merge_bin_files_and_pad(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_bin                   , OpTeeAndHeader_bin, Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_bin                          , 0x1000     , 0x20)
	ubootS =    Merge_bin_files_and_pad(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_bin             , UbootAndHeader_bin, Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_bin                    , 0x1000     , 0x20)
	# CP test, uncomment to init CP by bootblock:   cpS =       Merge_bin_files_and_pad(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_bin       , CpAndHeader_bin   , Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_cp_bin                 , 0x1000     , 0x20)
	imageS =    Merge_bin_files_and_pad(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_bin       , image_bin         , Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_linux_bin              , 0x400000   , 0x20)
	#romfsS =    Merge_bin_files_and_pad(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_linux_bin, romfs_bin         , tmp_bin                                                                    , 0x1000     , 0x20)
	#dtbS =      Merge_bin_files_and_pad(tmp_bin                                                      , dtb_bin           ,               Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_linux_bin, 0x1000     , 0x20)

	Merge_bin_files_and_pad(BootBlockAndHeader_bin                , BL31_AndHeader_bin, BootBlock_BL31_bin                   , 0x1000      , 0x20)
	Merge_bin_files_and_pad(BootBlock_BL31_bin                    , OpTeeAndHeader_bin, BootBlock_BL31_OpTee_bin             , 0x1000      , 0x20)
	Merge_bin_files_and_pad(BootBlock_BL31_OpTee_bin              , UbootAndHeader_bin, BootBlock_BL31_OpTee_uboot_bin       , 0x1000      , 0x20)
	Merge_bin_files_and_pad(BootBlockAndHeader_no_tip_bin         , BL31_AndHeader_bin, BootBlock_BL31_no_tip_bin            , 0x1000      , 0x20)
	Merge_bin_files_and_pad(BootBlock_BL31_no_tip_bin             , OpTeeAndHeader_bin, BootBlock_BL31_OpTee_no_tip_bin      , 0x1000      , 0x20)
	Merge_bin_files_and_pad(BootBlock_BL31_OpTee_no_tip_bin       , UbootAndHeader_bin, BootBlock_BL31_OpTee_uboot_no_tip_bin, 0x1000      , 0x20)
	Merge_bin_files_and_pad(BootBlock_BL31_OpTee_uboot_no_tip_bin , SA_Kmt_TipFwL0_bin, image_no_tip_SA_bin                  , 0x80000     , 0x20)
	
	
	# os.remove(tmp_bin)
	# os.remove(Kmt_TipFwL0_bin)
	if useSignedCombo0 is None:
		os.remove(Kmt_TipFwL0_Skmt_bin)
	os.remove(BootBlock_BL31_bin)
	os.remove(BootBlock_BL31_OpTee_bin)
	os.remove(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_bin)
	os.remove(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_bin)
	os.remove(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_bin)
	os.remove(BootBlock_BL31_no_tip_bin)
	os.remove(BootBlock_BL31_OpTee_no_tip_bin)

	startFl = 0x80000000
	print(("KMT starts at       "  + hex(startFl)+            " size " + hex(os.path.getsize(KmtAndHeader_bin))))
	print(("TFT L0 starts at    "  + hex(tipS_L0 + startFl) + " size " + hex(os.path.getsize(TipFwAndHeader_L0_bin))))
	print(("SKMT starts at      "  + hex(skmtS   + startFl) + " size " + hex(os.path.getsize(SkmtAndHeader_bin))))
	print(("TFT L1 starts at    "  + hex(tipS_L1 + startFl) + " size " + hex(os.path.getsize(TipFwAndHeader_L1_bin))))
	print(("BootBlock starts at "  + hex(bbS     + startFl) + " size " + hex(os.path.getsize(BootBlockAndHeader_bin))))
	print(("BL31 starts at      "  + hex(bl31S   + startFl) + " size " + hex(os.path.getsize(BL31_AndHeader_bin))))
	print(("OpTee starts at     "  + hex(OpTeeS  + startFl) + " size " + hex(os.path.getsize(OpTeeAndHeader_bin))))
	print(("Uboot starts at     "  + hex(ubootS  + startFl) + " size " + hex(os.path.getsize(UbootAndHeader_bin))))
	# CP test, uncomment to init CP by bootblock:   print ("CP starts at        "  + hex(cpS     + startFl) + " size " + hex(os.path.getsize(CpAndHeader_bin)))
	print(("image starts at     "  + hex(imageS  + startFl) + " size " + hex(os.path.getsize(image_bin))))
	# print ("romfs starts at     "+ hex(romfsS  + startFl) + " size " + hex(os.path.getsize(romfs_bin)))
	# print ("dtb starts at       "+ hex(dtbS    + startFl) + " size " + hex(os.path.getsize(dtb_bin)))
	

		
	startSA_TipFl = 0x80200000
	print(("No Tip KMT starts at       "  + hex(startSA_TipFl)+            " size " + hex(os.path.getsize(KmtAndHeader_bin))))
	print(("No Tip TFT L0 starts at    "  + hex(tipS_L0 + startFl) + " size " + hex(os.path.getsize(SA_TipFwAndHeader_L0_bin))))
	# Convert files to hex
	if (isPalladium):
		Convert_file_to_hex_like_PD_likes_it(BootBlockAndHeader_bin                      , BootBlockAndHeader_bin.replace(".bin"                      , ".hex"), 1)
		Convert_file_to_hex_like_PD_likes_it(UbootAndHeader_bin                          , UbootAndHeader_bin.replace(".bin"                          , ".hex"), 1)
		Convert_file_to_hex_like_PD_likes_it(TipFwAndHeader_L0_bin                       , TipFwAndHeader_L0_bin.replace(".bin"                       , ".hex"), 1)
		Convert_file_to_hex_like_PD_likes_it(TipFwAndHeader_L1_bin                       , TipFwAndHeader_L1_bin.replace(".bin"                       , ".hex"), 1)
		Convert_file_to_hex_like_PD_likes_it(KmtAndHeader_bin                            , KmtAndHeader_bin.replace(".bin"                            , ".hex"), 1)
		Convert_file_to_hex_like_PD_likes_it(CpAndHeader_bin                             , CpAndHeader_bin.replace(".bin"                             , ".hex"), 1)
		Convert_file_to_hex_like_PD_likes_it(Kmt_TipFwL0_Skmt_TipFwL1_bin                , Kmt_TipFwL0_Skmt_TipFwL1_bin.replace(".bin"                , ".hex"), 1)
		Convert_file_to_hex_like_PD_likes_it(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_bin      , Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_bin.replace(".bin"      , ".hex"), 1)
		Convert_file_to_hex_like_PD_likes_it(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_uboot_bin, Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_uboot_bin.replace(".bin", ".hex"), 1)

	
def Write_key_ind_and_key_mask_to_headers():
	# ECC
	# print ("skip*************************************************************")
	# Put the key mask number inside the header at offset 0x88 (132)
	Replace_binary_array(KmtAndHeader_bin,           0x88 , 2**(ord(otp_key_which_signs_kmt[-1]) - ord('0')) ,2, False , "KMT Header", True)
	Replace_binary_single_byte(TipFwAndHeader_L0_bin,   0x88, 2**(ord(kmt_key_which_signs_tip_fw_L0[-1]) - ord('0')), 1)
	Replace_binary_single_byte(TipFwAndHeader_L0_UT_bin,   0x88, 2**(ord(kmt_key_which_signs_tip_fw_L0[-1]) - ord('0')), 1)
	Replace_binary_single_byte(SA_TipFwAndHeader_L0_bin,0x88, 2**(ord(kmt_key_which_signs_tip_fw_L0[-1]) - ord('0')), 1)
	Replace_binary_single_byte(SkmtAndHeader_bin,      0x88, 2**(ord(kmt_key_which_signs_skmt[-1]) - ord('0')), 1)
	Replace_binary_single_byte(TipFwAndHeader_L1_bin,  0x88, 2**(ord(skmt_key_which_signs_tip_fw_L1[-1]) - ord('0')), 1)
	Replace_binary_single_byte(BootBlockAndHeader_bin, 0x88, 2**(ord(skmt_key_which_signs_bootblock[-1]) - ord('0')), 1)
	Replace_binary_single_byte(BL31_AndHeader_bin,     0x88, 2**(ord(skmt_key_which_signs_BL31[-1]) - ord('0')), 1)
	Replace_binary_single_byte(OpTeeAndHeader_bin,     0x88, 2**(ord(skmt_key_which_signs_OpTee[-1]) - ord('0')), 1)
	Replace_binary_single_byte(UbootAndHeader_bin,     0x88, 2**(ord(skmt_key_which_signs_uboot[-1]) - ord('0')), 1)
	
	# Put the key index number inside the header at offset 0x8c  (140)
	Replace_binary_single_byte(KmtAndHeader_bin,       0x8c, ord(otp_key_which_signs_kmt[-1]) - ord('0'))
	Replace_binary_single_byte(TipFwAndHeader_L0_bin,  0x8c, ord(kmt_key_which_signs_tip_fw_L0[-1]) - ord('0'))
	Replace_binary_single_byte(TipFwAndHeader_L0_UT_bin,  0x8c, ord(kmt_key_which_signs_tip_fw_L0[-1]) - ord('0'))
	Replace_binary_single_byte(SA_TipFwAndHeader_L0_bin,0x8c, ord(kmt_key_which_signs_tip_fw_L0[-1]) - ord('0'))        
	Replace_binary_single_byte(SkmtAndHeader_bin,      0x8c, ord(kmt_key_which_signs_skmt[-1]) - ord('0'))
	Replace_binary_single_byte(TipFwAndHeader_L1_bin,  0x8c, ord(skmt_key_which_signs_tip_fw_L1[-1]) - ord('0'))
	Replace_binary_single_byte(BootBlockAndHeader_bin, 0x8c, ord(skmt_key_which_signs_bootblock[-1]) - ord('0'))
	Replace_binary_single_byte(BL31_AndHeader_bin,     0x8c, ord(skmt_key_which_signs_BL31[-1]) - ord('0'))
	Replace_binary_single_byte(OpTeeAndHeader_bin,     0x8c, ord(skmt_key_which_signs_OpTee[-1]) - ord('0'))
	Replace_binary_single_byte(UbootAndHeader_bin,     0x8c, ord(skmt_key_which_signs_uboot[-1]) - ord('0'))
	

	# LMS :
	# Put the key index number inside the header at offset 196 and the key mask at 192
	if isLMS:
		# Put the key mask number inside the header at offset 0xc0  (192)
		Replace_binary_array(KmtAndHeader_bin, 0xc0, 2**(ord(lms_key_which_signs_kmt[-1]) - ord('0')), 2, False, "KMT Header", True)
		Replace_binary_single_byte(TipFwAndHeader_L0_bin, 0xc0, 2**(ord(lms_key_which_signs_tip_fw_L0[-1]) - ord('0')), 1)
		Replace_binary_single_byte(TipFwAndHeader_L0_UT_bin, 0xc0, 2**(ord(lms_key_which_signs_tip_fw_L0[-1]) - ord('0')), 1)
		Replace_binary_single_byte(SA_TipFwAndHeader_L0_bin, 0xc0, 2**(ord(lms_key_which_signs_tip_fw_L0[-1]) - ord('0')), 1)
		Replace_binary_single_byte(SkmtAndHeader_bin, 0xc0, 2**(ord(lms_key_which_signs_skmt[-1]) - ord('0')), 1)
		Replace_binary_single_byte(TipFwAndHeader_L1_bin, 0xc0, 2**(ord(lms_key_which_signs_tip_fw_L1[-1]) - ord('0')), 1)
		Replace_binary_single_byte(BootBlockAndHeader_bin, 0xc0, 2**(ord(lms_key_which_signs_bootblock[-1]) - ord('0')), 1)
		Replace_binary_single_byte(BL31_AndHeader_bin, 0xc0, 2**(ord(lms_key_which_signs_BL31[-1]) - ord('0')), 1)
		Replace_binary_single_byte(OpTeeAndHeader_bin, 0xc0, 2**(ord(lms_key_which_signs_OpTee[-1]) - ord('0')), 1)
		Replace_binary_single_byte(UbootAndHeader_bin, 0xc0, 2**(ord(lms_key_which_signs_uboot[-1]) - ord('0')), 1)
		
		# Put the key index number inside the header at offset 0xc4  (196)
		Replace_binary_single_byte(KmtAndHeader_bin, 0xc4, ord(otp_key_which_signs_kmt[-1]) - ord('0'))
		Replace_binary_single_byte(TipFwAndHeader_L0_bin, 0xc4, ord(lms_key_which_signs_tip_fw_L0[-1]) - ord('0'))
		Replace_binary_single_byte(TipFwAndHeader_L0_UT_bin, 0xc4, ord(lms_key_which_signs_tip_fw_L0[-1]) - ord('0'))
		Replace_binary_single_byte(SA_TipFwAndHeader_L0_bin, 0xc4, ord(lms_key_which_signs_tip_fw_L0[-1]) - ord('0'))
		Replace_binary_single_byte(SkmtAndHeader_bin, 0xc4, ord(lms_key_which_signs_skmt[-1]) - ord('0'))
		Replace_binary_single_byte(TipFwAndHeader_L1_bin, 0xc4, ord(lms_key_which_signs_tip_fw_L1[-1]) - ord('0'))
		Replace_binary_single_byte(BootBlockAndHeader_bin, 0xc4, ord(lms_key_which_signs_bootblock[-1]) - ord('0'))
		Replace_binary_single_byte(BL31_AndHeader_bin, 0xc4, ord(lms_key_which_signs_BL31[-1]) - ord('0'))
		Replace_binary_single_byte(OpTeeAndHeader_bin, 0xc4, ord(lms_key_which_signs_OpTee[-1]) - ord('0'))
		Replace_binary_single_byte(UbootAndHeader_bin, 0xc4, ord(lms_key_which_signs_uboot[-1]) - ord('0'))

def Write_LMS_flags_to_headers():

	kmt_keys_selected = any(config["lms_flags"][key] for key in config["key_groups"]["KMT_Keys"])

	if kmt_keys_selected:
		#LMS_KMO - the place in kmt header, address 128-129, in which the content should be 128* num of ECC keys, which is the offset of the first LMS KMT key in kmt LMS map xml 
		file_size = os.stat(kmt_map_tmp_bin).st_size #file_size =  128 * X + 80* X = (128+80) * X = 208 * X
		num_of_keys =  file_size // 208 
		start_lms_offset = 128 * num_of_keys

		# Extract the first byte 
		MSB = (start_lms_offset >> 8) & 0xFF
		# Extract the second byte 
		LSB = start_lms_offset & 0xFF
		Replace_binary_single_byte(KmtAndHeader_bin,       128, LSB, 0)
		Replace_binary_single_byte(KmtAndHeader_bin,       129, MSB, 0)
		
	if isLMS:
		# Creating variables dynamically
		lms_values = {key: 0x1 if value else 0x0 for key, value in config["lms_flags"].items()}

		# Using the values in function calls
		Replace_binary_single_byte(KmtAndHeader_bin,149, lms_values["is_LMS_kmt"], 0)
		Replace_binary_single_byte(SkmtAndHeader_bin,149, lms_values["is_LMS_skmt"], 0)
		Replace_binary_single_byte(TipFwAndHeader_L0_bin,149, lms_values["is_LMS_tip_fw_L0"], 0)
		Replace_binary_single_byte(TipFwAndHeader_L1_bin,149, lms_values["is_LMS_tip_fw_L1"], 0)
		Replace_binary_single_byte(BootBlockAndHeader_bin, 149, lms_values["is_LMS_bootblock"], 0)
		Replace_binary_single_byte(BL31_AndHeader_bin,149, lms_values["is_LMS_BL31"], 0)
		Replace_binary_single_byte(OpTeeAndHeader_bin,149, lms_values["is_LMS_OpTee"], 0)
		Replace_binary_single_byte(UbootAndHeader_bin,149, lms_values["is_LMS_uboot"], 0)


def Write_timestamp_and_IV_to_headers():
	# insert timestamp to header:
	cur_ticks = int(time.time()) % 0xFFFFFFFF
	
	Replace_binary_array(KmtAndHeader_bin             , 0xBC,   cur_ticks, 4, True, "KMT       add timestamp")
	Replace_binary_array(TipFwAndHeader_L0_bin        , 0xBC,   cur_ticks, 4, True, "L0        add timestamp")
	Replace_binary_array(SkmtAndHeader_bin            , 0xBC,   cur_ticks, 4, True, "SKMT      add timestamp")
	Replace_binary_array(SA_TipFwAndHeader_L0_bin      , 0xBC,   cur_ticks, 4, True, "L0        add timestamp")        
	Replace_binary_array(TipFwAndHeader_L1_bin        , 0xBC,   cur_ticks, 4, True, "L1        add timestamp")
	Replace_binary_array(BootBlockAndHeader_bin       , 0xBC,   cur_ticks, 4, True, "Bootblock add timestamp")
	Replace_binary_array(BootBlockAndHeader_no_tip_bin, 0xBC,   cur_ticks, 4, True, "Bootblock add timestamp")
	Replace_binary_array(BL31_AndHeader_bin           , 0xBC,   cur_ticks, 4, True, "BL31      add timestamp")
	Replace_binary_array(OpTeeAndHeader_bin           , 0xBC,   cur_ticks, 4, True, "OpTee     add timestamp")
	Replace_binary_array(UbootAndHeader_bin           , 0xBC,   cur_ticks, 4, True, "UBOOT     add timestamp")

	# insert AES IV to each header. IV includes both timestamp and the hash of the image with the timestamp in it.
	tick_arr = bytes.fromhex(format(cur_ticks, '08x'))
	
	Replace_binary_array(TipFwAndHeader_L0_bin        , 0xAC,   bytes(tick_arr + bin_calc_hash(TipFwAndHeader_L0_bin  , 12)), 16, False, "L0        add IV")
	Replace_binary_array(TipFwAndHeader_L1_bin        , 0xAC,   bytes(tick_arr + bin_calc_hash(TipFwAndHeader_L1_bin  , 12)), 16, False, "L1        add IV")
	Replace_binary_array(BootBlockAndHeader_bin       , 0xAC,   bytes(tick_arr + bin_calc_hash(BootBlockAndHeader_bin , 12)), 16, False, "Bootblock add IV")
	Replace_binary_array(BL31_AndHeader_bin           , 0xAC,   bytes(tick_arr + bin_calc_hash(BL31_AndHeader_bin     , 12)), 16, False, "BL31      add IV")
	Replace_binary_array(OpTeeAndHeader_bin           , 0xAC,   bytes(tick_arr + bin_calc_hash(OpTeeAndHeader_bin     , 12)), 16, False, "OpTee     add IV")
	Replace_binary_array(UbootAndHeader_bin           , 0xAC,   bytes(tick_arr + bin_calc_hash(UbootAndHeader_bin     , 12)), 16, False, "UBOOT     add IV")


def MoveToFolder(isPalladium, dstFolder):
	if (isPalladium):
		move(KmtAndHeader_bin.replace(".bin"                            , ".hex"), dstFolder)
		move(SkmtAndHeader_bin.replace(".bin"                           , ".hex"), dstFolder)
		move(TipFwAndHeader_L0_bin.replace(".bin"                       , ".hex"), dstFolder)
		move(TipFwAndHeader_L0_UT_bin.replace(".bin"                    , ".hex"), dstFolder)
		move(SA_TipFwAndHeader_L0_bin.replace(".bin"                    , ".hex"), dstFolder)
		move(UbootAndHeader_L1_bin.replace(".bin"                       , ".hex"), dstFolder)
		move(BootBlockAndHeader_bin.replace(".bin"                      , ".hex"), dstFolder)
		move(CpAndHeader_bin.replace(".bin"                             , ".hex"), dstFolder)
		move(Kmt_TipFwL0_Skmt_TipFwL1_bin.replace(".bin"                , ".hex"), dstFolder)
		move(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_bin.replace(".bin"      , ".hex"), dstFolder)
		move(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_uboot_bin.replace(".bin", ".hex"), dstFolder)
		# CP test, uncomment to init CP by bootblock:   move(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_uboot_cp_bin.replace(".bin", ".hex"), dstFolder)
		
	CheckIfFileExistsAndMove(KmtAndHeader_bin                                                 , dstFolder)
	CheckIfFileExistsAndMove(SkmtAndHeader_bin                                                , dstFolder)
	CheckIfFileExistsAndMove(TipFwAndHeader_L0_bin                                            , dstFolder)
	CheckIfFileExistsAndMove(TipFwAndHeader_L0_UT_bin                                         , dstFolder)
	CheckIfFileExistsAndMove(SA_TipFwAndHeader_L0_bin                                         , dstFolder)
	CheckIfFileExistsAndMove(TipFwAndHeader_L1_bin                                            , dstFolder)
	CheckIfFileExistsAndMove(UbootAndHeader_bin                                               , dstFolder)
	CheckIfFileExistsAndMove(BootBlockAndHeader_bin                                           , dstFolder)
	CheckIfFileExistsAndMove(BootBlockAndHeader_no_tip_bin                                    , dstFolder)
	CheckIfFileExistsAndMove(BL31_AndHeader_bin                                               , dstFolder)
	CheckIfFileExistsAndMove(OpTeeAndHeader_bin                                               , dstFolder)
	CheckIfFileExistsAndMove(CpAndHeader_bin                                                  , dstFolder)
	CheckIfFileExistsAndMove(Kmt_TipFwL0_bin                                                  , dstFolder)
	CheckIfFileExistsAndMove(Kmt_TipFwL0_UT_bin                                               , dstFolder)
	CheckIfFileExistsAndMove(SA_Kmt_TipFwL0_bin                                               , dstFolder)
	# CheckIfFileExistsAndMove(Kmt_TipFwL0_Skmt_bin                                             , dstFolder)
	CheckIfFileExistsAndMove(Kmt_TipFwL0_Skmt_TipFwL1_bin                                     , dstFolder)
	# CheckIfFileExistsAndMove(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_bin                           , dstFolder)
	# CheckIfFileExistsAndMove(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_bin                      , dstFolder)
	# CheckIfFileExistsAndMove(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_bin                , dstFolder)
	CheckIfFileExistsAndMove(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_bin          , dstFolder)
	# CP test, uncomment to init CP by bootblock:   CheckIfFileExistsAndMove(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_cp_bin       , dstFolder)
	CheckIfFileExistsAndMove(BootBlock_BL31_OpTee_uboot_bin                                   , dstFolder)
	CheckIfFileExistsAndMove(BootBlock_BL31_OpTee_uboot_no_tip_bin                            , dstFolder)
	CheckIfFileExistsAndMove(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_linux_bin    , dstFolder)
	CheckIfFileExistsAndMove(image_no_tip_SA_bin                                              , dstFolder)

# Dynamically generate keys based on configuration
generated_keys = set()

def generate_single_LMS_key(key, TypeOfKey_TIP, pinCode):
	if key in generated_keys:
		return
	generated_keys.add(key)

	key_parts = key.split('_')
	key_name = config[f"lms_key_which_signs_{'_'.join(key_parts[2:])}"]
	key_path, key_id = key_paths[key_name]
	GenerateKeyLMS(key_path, TypeOfKey_TIP, pinCode, key_id)

def generate_group(group ,TypeOfKey, TypeOfKey_TIP,  pinCode):
	for key in group:
		generate_single_LMS_key(key, TypeOfKey_TIP, pinCode)

def Generate_Or_Load_Keys(TypeOfKey, TypeOfKey_TIP, TypeOfKey_BMC, pinCode):
	if TypeOfKey != "RemoteHSM":
		if any(config["lms_flags"].values()):
			print("Generate all LMS keys")

		for key, value in config["lms_flags"].items():
			if value:
				if key in config["key_groups"]["KMT_Keys"]:
					generate_group(config["key_groups"]["KMT_Keys"], TypeOfKey, TypeOfKey_TIP, pinCode)
				elif key in config["key_groups"]["SKMT_Keys"]:
					generate_group(config["key_groups"]["SKMT_Keys"], TypeOfKey, TypeOfKey_TIP, pinCode)
				else:
					generate_single_LMS_key(key, TypeOfKey_TIP, pinCode)

		print("Generate Manifest RSA keys")
		GenerateKeyRSA(rsa_key0, TypeOfKey, pinCode, id_rsa_key0)
		
		# Genearte Fuse Array
		print("Generate OTP keys")
		GenerateKeyECC(otp_key0, TypeOfKey, pinCode, id_otp_key0)
		GenerateKeyECC(otp_key1, TypeOfKey, pinCode, id_otp_key1)
		GenerateKeyECC(otp_key2, TypeOfKey, pinCode, id_otp_key2)
		GenerateKeyECC(otp_key3, TypeOfKey, pinCode, id_otp_key3)
		GenerateKeyECC(otp_key4, TypeOfKey, pinCode, id_otp_key4)
		GenerateKeyECC(otp_key5, TypeOfKey, pinCode, id_otp_key5)
		GenerateKeyECC(otp_key6, TypeOfKey, pinCode, id_otp_key6)
		GenerateKeyECC(otp_key7, TypeOfKey, pinCode, id_otp_key7)
		GenerateKeyECC(otp_key8, TypeOfKey, pinCode, id_otp_key8)

	if(os.path.isfile(arbel_fuse_map_xml) == True):
		print("Generate OTP image")
		Generate_binary(arbel_fuse_map_xml, arbel_fuse_map_bin)
	else:
		print("Skip OTP generation")
	# Generate Key Manifest

	if TypeOfKey != "RemoteHSM":
		print("Generate KMT ECC keys")
		GenerateKeyECC(kmt_key0, TypeOfKey_TIP, pinCode, id_kmt_key0)
		GenerateKeyECC(kmt_key1, TypeOfKey_TIP, pinCode, id_kmt_key1)
	
	if TypeOfKey != "RemoteHSM":
		print("Generate SKMT ECC keys")
		GenerateKeyECC(skmt_key0, TypeOfKey_TIP, pinCode, id_skmt_key0)
		GenerateKeyECC(skmt_key1, TypeOfKey_BMC, pinCode, id_skmt_key1)
		GenerateKeyECC(skmt_key4, TypeOfKey_BMC, pinCode, id_skmt_key4)

def Hardening_all_images():
	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	try:
		# parse chip MXL file:
		registers = Register_file_chip_xml_parse(chip_xml)
		
		# Create binaries of register files:
		Register_csv_file_handler(registers_L1           , bin_registers_L1        , registers)
		Register_csv_file_handler(registers_bootblock    , bin_registers_bootblock , registers)
		Register_csv_file_handler(registers_bl31         , bin_registers_bl31      , registers)
		Register_csv_file_handler(registers_optee        , bin_registers_optee     , registers)
		Register_csv_file_handler(registers_uboot        , bin_registers_uboot     , registers)
	except (Exception) as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print(("\n Hardening_all_images: Error (%s)" % str(e)))
		raise
	finally:
		os.chdir(currpath)

# build a single image and register file. If no register file is available reg binary is empty
def Build_single_image_with_regs(bin_file, reg_bin_img):
	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	
	output_file = os.path.join(tmp_outputs_dir, os.path.split(bin_file)[1])

	try:
		# if no register file, just copy it to temp dir.
		if (os.path.isfile(reg_bin_img) == False):
			print ("File " , reg_bin_img, " not found, copy ", bin_file, " to ", output_file, "\n")
			copyfile(bin_file, output_file)
			return 0xFFFFFFFF
			
		# append register file and same the output to tmp dir
		else:
			offset = Merge_bin_files_and_pad(bin_file, reg_bin_img, output_file, 0x10, 0x10, 0x10)
			print ("Output file ", output_file, " merged with ", reg_bin_img, " offset is " , hex(offset), "\n")
			return offset
	except (Exception) as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print(("\n IGPS_common.py: Error building basic binaries (%s)" % str(e)))
		raise

	finally:
		os.chdir(currpath)

def Build_basic_images():

	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	try:
		# check inputs and align if needed:
		
		print("\nAlign input images\n")
		Pad_bin_file_inplace(  bb_bin         ,  32)
		Pad_bin_file_inplace(  bb_bin_no_tip  ,  32)
		Pad_bin_file_inplace(  uboot_bin      ,  32)
		Pad_bin_file_inplace(  tee_bin        ,  32)
		Pad_bin_file_inplace(  bl31_bin       ,  32)
		Pad_bin_file_inplace(  Tip_FW_L0_bin  ,  32)
		Pad_bin_file_inplace(  Tip_FW_L0_UT_bin  ,  32)
		Pad_bin_file_inplace(  SA_Tip_FW_L0_bin ,32)
		Pad_bin_file_inplace(  Tip_FW_L1_bin  ,  32)
		Pad_bin_file_inplace(  CP_FW_bin      ,  32)

		# Generate kmt and skmt map files (no headers)	
		
		kmt_keys_selected = any(config["lms_flags"][key] for key in config["key_groups"]["KMT_Keys"])

		if kmt_keys_selected:
			Generate_binary(kmt_map_lms_xml, kmt_map_tmp_bin)
		else:
			Generate_binary(kmt_map_xml, kmt_map_tmp_bin)
			
		skmt_keys_selected = any(config["lms_flags"][key] for key in config["key_groups"]["SKMT_Keys"])
		if skmt_keys_selected:
			Generate_binary(skmt_map_lms_xml, skmt_map_tmp_bin)
		else:
			Generate_binary(skmt_map_xml, skmt_map_tmp_bin)
		
		Pad_bin_file_inplace(  kmt_map_tmp_bin       ,  16)
		Pad_bin_file_inplace(  skmt_map_tmp_bin      ,  32)
		
		Generate_binary(KmtAndHeader_xml             , KmtAndHeader_bin)
		Generate_binary(SkmtAndHeader_xml            , SkmtAndHeader_bin)

		# copy FWs without register to tmp folder 
		copyfile(Tip_FW_L0_bin, Tip_FW_L0_tmp_bin)
		copyfile(bb_bin_no_tip, bb_tmp_bin_no_tip)
		copyfile(SA_Tip_FW_L0_bin, SA_Tip_FW_L0_tmp_bin)
		copyfile(Tip_FW_L0_UT_bin, Tip_FW_L0_UT_tmp_bin)

		# append registers files if they are there. If not - just cop to tmp folder:
		offset_L1    = Build_single_image_with_regs(Tip_FW_L1_bin,  bin_registers_L1        )
		offset_bb    = Build_single_image_with_regs(bb_bin,         bin_registers_bootblock )
		offset_bl31  = Build_single_image_with_regs(bl31_bin,       bin_registers_bl31      )
		offset_tee   = Build_single_image_with_regs(tee_bin,        bin_registers_optee     )
		offset_uboot = Build_single_image_with_regs(uboot_bin,      bin_registers_uboot     )

		Generate_binary(TipFwAndHeader_L0_xml        , TipFwAndHeader_L0_bin)
		Generate_binary(TipFwAndHeader_L0_UT_xml, TipFwAndHeader_L0_UT_bin)
		Generate_binary(SA_TipFwAndHeader_L0_xml     , SA_TipFwAndHeader_L0_bin)
		Generate_binary(TipFwAndHeader_L1_xml        , TipFwAndHeader_L1_bin)
		Generate_binary(BootBlockAndHeader_xml       , BootBlockAndHeader_bin)
		Generate_binary(BootBlockAndHeader_no_tip_xml, BootBlockAndHeader_no_tip_bin)
		Generate_binary(BL31_AndHeader_xml           , BL31_AndHeader_bin)
		Generate_binary(OpTeeAndHeader_xml           , OpTeeAndHeader_bin)
		Generate_binary(UbootAndHeader_xml           , UbootAndHeader_bin)
		Generate_binary(CpAndHeader_xml              , CpAndHeader_bin)

		if (offset_L1 != 0xFFFFFFFF):
			Replace_binary_array(TipFwAndHeader_L1_bin,  0x1B4, offset_L1             , 4, True, "TIP L1 reg offset")
			
		if (offset_bb != 0xFFFFFFFF):
			Replace_binary_array(BootBlockAndHeader_bin, 0x1B4, offset_bb             , 4, True, "bootblock reg offset")
			
		if (offset_bl31 != 0xFFFFFFFF):
			Replace_binary_array(BL31_AndHeader_bin,     0x1B4, offset_bl31             , 4, True, "bl31 reg offset")
			
		if (offset_tee != 0xFFFFFFFF):
			Replace_binary_array(OpTeeAndHeader_bin,     0x1B4, offset_tee             , 4, True, "optee reg offset")
			
		if (offset_uboot != 0xFFFFFFFF):
			Replace_binary_array(UbootAndHeader_bin,     0x1B4, offset_uboot             , 4, True, "uboot reg offset")
		
	except (Exception) as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print(("\n IGPS_common.py: Error building basic binaries (%s)" % str(e)))
		raise

	finally:
		os.chdir(currpath)

def Write_CRC_to_TIP_images():

	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	try:
		# check inputs and align if needed:
		
		print("\Add CRC to TIP images only\n")
		
		CRC32_binary(KmtAndHeader_bin           , 112    , 12     , KmtAndHeader_bin)
		CRC32_binary(TipFwAndHeader_L0_bin      , 112    , 12     , TipFwAndHeader_L0_bin)
		CRC32_binary(TipFwAndHeader_L0_UT_bin   , 112    , 12     , TipFwAndHeader_L0_UT_bin)
		CRC32_binary(SA_TipFwAndHeader_L0_bin   , 112    , 12     , SA_TipFwAndHeader_L0_bin)        
		CRC32_binary(TipFwAndHeader_L1_bin      , 112    , 12     , TipFwAndHeader_L1_bin)
		
	except (Exception) as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print(("\n IGPS_common.py, Write_CRC_to_TIP_images Error building basic binaries (%s)" % str(e)))
		raise

	finally:
		os.chdir(currpath)
       

def Sign_combo0(TypeOfKey, pinCode, isPalladium, TypeOfKey_TIP=None, TypeOfKey_BMC=None):

	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	try:
		if TypeOfKey == "RemoteHSM":
			# Embed_external_sig(sig_der             , binfile                     , outputFile            , embed_signature)
			Embed_external_sig(KmtAndHeader_der      ,KmtAndHeader_lms_sig_bin,  KmtAndHeader_basic_bin      , KmtAndHeader_bin      , 16, config["lms_flags"]["is_LMS_kmt"])
			Embed_external_sig(TipFwAndHeader_L0_der , TipFwAndHeader_L0_lms_sig_bin, TipFwAndHeader_L0_basic_bin , TipFwAndHeader_L0_bin , 16, config["lms_flags"]["is_LMS_tip_fw_L0"])
			Embed_external_sig(SA_TipFwAndHeader_L0_der ,SA_TipFwAndHeader_L0_lms_sig_bin, SA_TipFwAndHeader_L0_basic_bin ,SA_TipFwAndHeader_L0_bin , 16, False)
			Embed_external_sig(SkmtAndHeader_der     , SkmtAndHeader_lms_sig_bin, SkmtAndHeader_basic_bin     , SkmtAndHeader_bin     , 16, config["lms_flags"]["is_LMS_skmt"])
			Embed_external_sig(TipFwAndHeader_L1_der , TipFwAndHeader_L1_lms_sig_bin, TipFwAndHeader_L1_basic_bin , TipFwAndHeader_L1_bin , 16, config["lms_flags"]["is_LMS_tip_fw_L1"])
		else:
			
			# Sign Images of TIP
			Sign_binary(KmtAndHeader_basic_bin,       112, eval(otp_key_which_signs_kmt),        16, KmtAndHeader_bin,       TypeOfKey_TIP, pinCode, eval("id_otp_key" + otp_key_which_signs_kmt[-1]), isECC, config["lms_flags"]["is_LMS_kmt"] , key_paths[lms_key_which_signs_kmt][0])
			Sign_binary(TipFwAndHeader_L0_basic_bin,  112, eval(kmt_key_which_signs_tip_fw_L0),  16, TipFwAndHeader_L0_bin,  TypeOfKey_TIP, pinCode, eval("id_kmt_key" + kmt_key_which_signs_tip_fw_L0[-1]), isECC, config["lms_flags"]["is_LMS_tip_fw_L0"] ,key_paths[lms_key_which_signs_tip_fw_L0][0])
			Sign_binary(SA_TipFwAndHeader_L0_basic_bin,  112, eval(kmt_key_which_signs_tip_fw_L0),  16, SA_TipFwAndHeader_L0_bin,  TypeOfKey_TIP, pinCode, eval("id_kmt_key" + kmt_key_which_signs_tip_fw_L0[-1]), isECC, False, 0)
			Sign_binary(TipFwAndHeader_L0_UT_basic_bin,  112, eval(kmt_key_which_signs_tip_fw_L0),  16, TipFwAndHeader_L0_UT_bin,  TypeOfKey_TIP, pinCode, eval("id_kmt_key" + kmt_key_which_signs_tip_fw_L0[-1]), isECC, False, 0)
			Sign_binary(SkmtAndHeader_basic_bin,      112, eval(kmt_key_which_signs_skmt),       16, SkmtAndHeader_bin,      TypeOfKey_TIP, pinCode, eval("id_kmt_key" + kmt_key_which_signs_skmt[-1]), isECC, config["lms_flags"]["is_LMS_skmt"] ,key_paths[lms_key_which_signs_skmt][0])
			Sign_binary(TipFwAndHeader_L1_basic_bin,  112, eval(skmt_key_which_signs_tip_fw_L1), 16, TipFwAndHeader_L1_bin,  TypeOfKey_TIP, pinCode, eval("id_skmt_key" + skmt_key_which_signs_tip_fw_L1[-1]), isECC, config["lms_flags"]["is_LMS_tip_fw_L1"] ,key_paths[lms_key_which_signs_tip_fw_L1][0])
			
			# remove CRC
			# Note: secure image will hold both CRC and signature, so that same
			# bins will work both on basic and secure.
			
			# CRC32_remove(KmtAndHeader_bin          , 112    , 12     , KmtAndHeader_bin)
			# CRC32_remove(TipFwAndHeader_L0_bin     , 112    , 12     , TipFwAndHeader_L0_bin)
			# CRC32_remove(TipFwAndHeader_L1_bin     , 112    , 12     , TipFwAndHeader_L1_bin)

	except (Exception) as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print(("\n GenerateImages.py: Error signing binaries (%s)" % str(e)))
		raise

	finally:
		os.chdir(currpath)
		
		
		

def Sign_combo1(TypeOfKey, pinCode, isPalladium, TypeOfKey_TIP=None, TypeOfKey_BMC=None):

	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	try:
		if TypeOfKey == "RemoteHSM":
			# Embed_external_sig(sig_der             , binfile                     , outputFile            , embed_signature)
			# BMC bootloaders not verified now. Use tip l1 signature for builds for now
			Embed_external_sig(BootBlockAndHeader_der, BootBlockAndHeader_lms_sig_bin, BootBlockAndHeader_basic_bin, BootBlockAndHeader_bin, 16, config["lms_flags"]["is_LMS_bootblock"])
			Embed_external_sig(BL31_AndHeader_der    , BL31_AndHeader_lms_sig_bin, BL31_AndHeader_basic_bin    , BL31_AndHeader_bin    , 16, config["lms_flags"]["is_LMS_uboot"])
			Embed_external_sig(OpTeeAndHeader_der    , OpTeeAndHeader_lms_sig_bin,  OpTeeAndHeader_basic_bin    , OpTeeAndHeader_bin    , 16, config["lms_flags"]["is_LMS_OpTee"])
			Embed_external_sig(UbootAndHeader_der    , UbootAndHeader_lms_sig_bin , UbootAndHeader_basic_bin    , UbootAndHeader_bin    , 16, config["lms_flags"]["is_LMS_BL31"])

		else:
			# Sign Images of BMC
			Sign_binary(BootBlockAndHeader_basic_bin, 112, eval(skmt_key_which_signs_bootblock), 16, BootBlockAndHeader_bin, TypeOfKey_BMC, pinCode, eval("id_skmt_key" + skmt_key_which_signs_bootblock[-1]),isECC, config["lms_flags"]["is_LMS_bootblock"] ,key_paths[lms_key_which_signs_bootblock][0])
			Sign_binary(UbootAndHeader_basic_bin,     112, eval(skmt_key_which_signs_uboot),     16, UbootAndHeader_bin,     TypeOfKey_BMC, pinCode, eval("id_skmt_key" + skmt_key_which_signs_uboot[-1]),isECC, config["lms_flags"]["is_LMS_uboot"] ,key_paths[lms_key_which_signs_uboot][0])
			Sign_binary(OpTeeAndHeader_basic_bin,     112, eval(skmt_key_which_signs_OpTee),     16, OpTeeAndHeader_bin,     TypeOfKey_BMC, pinCode, eval("id_skmt_key" + skmt_key_which_signs_OpTee[-1]),isECC, config["lms_flags"]["is_LMS_OpTee"] ,key_paths[lms_key_which_signs_OpTee][0])
			Sign_binary(BL31_AndHeader_basic_bin,     112, eval(skmt_key_which_signs_BL31),      16, BL31_AndHeader_bin,     TypeOfKey_BMC, pinCode, eval("id_skmt_key" + skmt_key_which_signs_BL31[-1]),isECC, config["lms_flags"]["is_LMS_BL31"] ,key_paths[lms_key_which_signs_BL31][0])

	except (Exception) as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print(("\n GenerateImages.py: Error signing binaries (%s)" % str(e)))
		raise

	finally:
		os.chdir(currpath)



def Merge_signed_files(isPalladium, useSignedCombo0):

	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	try:
		MergeBinFilesAndPadAndPrint(isPalladium, useSignedCombo0)
		# Move Secure images to Secure Directory
		MoveToFolder(isPalladium, secure_outputs_dir)
		# need to remove the no tip secure bin that was created in last operation of moving all from basic to secure
		os.remove(BootBlock_BL31_OpTee_uboot_secure_no_tip_bin)
	except (Exception) as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print(("\n GenerateImages.py: Error signing binaries (%s)" % str(e)))
		raise

	finally:
		os.chdir(currpath)

