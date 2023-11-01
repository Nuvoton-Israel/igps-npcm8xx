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


kmtS          =   0xFFFFFFFF
tipS_L0       =   0xFFFFFFFF
saTipS_L0     =   0xFFFFFFFF
skmtS         =   0xFFFFFFFF
tipS_L1       =   0xFFFFFFFF
bbS           =   512*1024
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
	except (Exception) as e:
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
		
		
		bbS =  512*1024
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


def MergeBinFilesAndPadAndPrint(isPalladium):
	# Merge files
	bbS = 512*1024
	
	tipS_L0 =   Merge_bin_files_and_pad(KmtAndHeader_bin            , TipFwAndHeader_L0_bin    , Kmt_TipFwL0_bin                       , 0x1000, 0x20)
	sa_tipS_L0 =   Merge_bin_files_and_pad(KmtAndHeader_bin         , SA_TipFwAndHeader_L0_bin , SA_Kmt_TipFwL0_bin                    , 0x1000, 0x20)
	skmtS  =    Merge_bin_files_and_pad(Kmt_TipFwL0_bin             , SkmtAndHeader_bin        , Kmt_TipFwL0_Skmt_bin                  , 0x1000, 0x20)
	tipS_L1 =   Merge_bin_files_and_pad(Kmt_TipFwL0_Skmt_bin        , TipFwAndHeader_L1_bin    , Kmt_TipFwL0_Skmt_TipFwL1_bin          , 0x1000, 0x20)
	bbS =       Merge_bin_files_and_pad(Kmt_TipFwL0_Skmt_TipFwL1_bin, BootBlockAndHeader_bin   , Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_bin, bbS   , 0x20)
	
	# check that bootblock is still at 512KB offset
	if (bbS != 512*1024):
		print("       =============   ERROR: TIP_FW overflow ======================")
		
	bl31S  =    Merge_bin_files_and_pad(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_bin                        , BL31_AndHeader_bin, Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_bin                                , 0x1000     , 0x20)
	OpTeeS =    Merge_bin_files_and_pad(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_bin                   , OpTeeAndHeader_bin, Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_bin                          , 0x1000     , 0x20)
	ubootS =    Merge_bin_files_and_pad(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_bin             , UbootAndHeader_bin, Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_bin                    , 0x1000     , 0x20)
	# cpS =       Merge_bin_files_and_pad(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_bin     , CpAndHeader_bin   , Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_cp_bin                 , 0x1000     , 0x20)
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
	#print ("CP starts at        "  + hex(cpS     + startFl) + " size " + hex(os.path.getsize(CpAndHeader_bin)))
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


def MoveToFolder(isPalladium, dstFolder):
	if (isPalladium):
		move(KmtAndHeader_bin.replace(".bin"                            , ".hex"), dstFolder)
		move(SkmtAndHeader_bin.replace(".bin"                           , ".hex"), dstFolder)
		move(TipFwAndHeader_L0_bin.replace(".bin"                       , ".hex"), dstFolder)
		move(SA_TipFwAndHeader_L0_bin.replace(".bin"                    , ".hex"), dstFolder)
		move(UbootAndHeader_L1_bin.replace(".bin"                       , ".hex"), dstFolder)
		move(BootBlockAndHeader_bin.replace(".bin"                      , ".hex"), dstFolder)
		move(CpAndHeader_bin.replace(".bin"                             , ".hex"), dstFolder)
		move(Kmt_TipFwL0_Skmt_TipFwL1_bin.replace(".bin"                , ".hex"), dstFolder)
		move(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_bin.replace(".bin"      , ".hex"), dstFolder)
		move(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_uboot_bin.replace(".bin", ".hex"), dstFolder)
		
	CheckIfFileExistsAndMove(KmtAndHeader_bin                                                 , dstFolder)
	CheckIfFileExistsAndMove(SkmtAndHeader_bin                                                , dstFolder)
	CheckIfFileExistsAndMove(TipFwAndHeader_L0_bin                                            , dstFolder)
	CheckIfFileExistsAndMove(SA_TipFwAndHeader_L0_bin                                         , dstFolder)
	CheckIfFileExistsAndMove(TipFwAndHeader_L1_bin                                            , dstFolder)
	CheckIfFileExistsAndMove(UbootAndHeader_bin                                               , dstFolder)
	CheckIfFileExistsAndMove(BootBlockAndHeader_bin                                           , dstFolder)
	CheckIfFileExistsAndMove(BootBlockAndHeader_no_tip_bin                                    , dstFolder)
	CheckIfFileExistsAndMove(BL31_AndHeader_bin                                               , dstFolder)
	CheckIfFileExistsAndMove(OpTeeAndHeader_bin                                               , dstFolder)
	CheckIfFileExistsAndMove(CpAndHeader_bin                                                  , dstFolder)
	CheckIfFileExistsAndMove(Kmt_TipFwL0_bin                                                  , dstFolder)
	CheckIfFileExistsAndMove(SA_Kmt_TipFwL0_bin                                               , dstFolder)
	# CheckIfFileExistsAndMove(Kmt_TipFwL0_Skmt_bin                                             , dstFolder)
	CheckIfFileExistsAndMove(Kmt_TipFwL0_Skmt_TipFwL1_bin                                     , dstFolder)
	# CheckIfFileExistsAndMove(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_bin                           , dstFolder)
	# CheckIfFileExistsAndMove(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_bin                      , dstFolder)
	# CheckIfFileExistsAndMove(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_bin                , dstFolder)
	CheckIfFileExistsAndMove(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_bin          , dstFolder)
	CheckIfFileExistsAndMove(BootBlock_BL31_OpTee_uboot_bin                                   , dstFolder)
	CheckIfFileExistsAndMove(BootBlock_BL31_OpTee_uboot_no_tip_bin                            , dstFolder)
	CheckIfFileExistsAndMove(Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_linux_bin    , dstFolder)
	CheckIfFileExistsAndMove(image_no_tip_SA_bin                                              , dstFolder)


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
		# openssl: :use openssl for both images
		else:	
			TypeOfKey_TIP = TypeOfKey
			TypeOfKey_BMC = TypeOfKey
		
		Run_Init()
		
		if TypeOfKey != "RemoteHSM":
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
			print("Generate KMT keys")
			GenerateKeyECC(kmt_key0, TypeOfKey_TIP, pinCode, id_kmt_key0)
			GenerateKeyECC(kmt_key1, TypeOfKey_TIP, pinCode, id_kmt_key1)

		Generate_binary(kmt_map_xml, kmt_map_bin)
		
		if TypeOfKey != "RemoteHSM":
			print("Generate SKMT keys")
			GenerateKeyECC(skmt_key0, TypeOfKey_TIP, pinCode, id_skmt_key0)
			GenerateKeyECC(skmt_key1, TypeOfKey_BMC, pinCode, id_skmt_key1)
			GenerateKeyECC(skmt_key2, TypeOfKey_BMC, pinCode, id_skmt_key2)
			GenerateKeyECC(skmt_key3, TypeOfKey_BMC, pinCode, id_skmt_key3)
			GenerateKeyECC(skmt_key4, TypeOfKey_BMC, pinCode, id_skmt_key4)

		Generate_binary(skmt_map_xml, skmt_bin)
		
		
		
		# check inputs and align if needed:
		
		print("\nAlign input images\n")
		Pad_bin_file_inplace(  bb_bin         ,  32)
		Pad_bin_file_inplace(  bb_bin_no_tip  ,  32)
		Pad_bin_file_inplace(  uboot_bin      ,  32)
		Pad_bin_file_inplace(  tee_bin        ,  32)
		Pad_bin_file_inplace(  bl31_bin       ,  32)
		Pad_bin_file_inplace(  image_bin      ,  32)
		Pad_bin_file_inplace(  romfs_bin      ,  32)
		Pad_bin_file_inplace(  dtb_bin        ,  32)
		Pad_bin_file_inplace(  Tip_FW_L0_bin  ,  32)
		Pad_bin_file_inplace(  SA_Tip_FW_L0_bin ,32)
		Pad_bin_file_inplace(  skmt_bin       ,  32)
		Pad_bin_file_inplace(  Tip_FW_L1_bin  ,  32)
		Pad_bin_file_inplace(  CP_FW_bin      ,  32)
		
		# Generate Basic Images
		Generate_binary(KmtAndHeader_xml             , KmtAndHeader_bin)
		Generate_binary(TipFwAndHeader_L0_xml        , TipFwAndHeader_L0_bin)
		Generate_binary(SA_TipFwAndHeader_L0_xml        , SA_TipFwAndHeader_L0_bin)
		Generate_binary(SkmtAndHeader_xml            , SkmtAndHeader_bin)
		Generate_binary(TipFwAndHeader_L1_xml        , TipFwAndHeader_L1_bin)
		Generate_binary(BootBlockAndHeader_xml       , BootBlockAndHeader_bin)
		Generate_binary(BootBlockAndHeader_no_tip_xml, BootBlockAndHeader_no_tip_bin)
		Generate_binary(BL31_AndHeader_xml           , BL31_AndHeader_bin)
		Generate_binary(OpTeeAndHeader_xml           , OpTeeAndHeader_bin)
		Generate_binary(UbootAndHeader_xml           , UbootAndHeader_bin)
		Generate_binary(CpAndHeader_xml              , CpAndHeader_bin)
		
		
		# Put the key index number inside the header at offset 140
		Replace_binary_single_byte(KmtAndHeader_bin,       140, ord(otp_key_which_signs_kmt[-1]) - ord('0'))
		Replace_binary_single_byte(TipFwAndHeader_L0_bin,  140, ord(kmt_key_which_signs_tip_fw_L0[-1]) - ord('0'))
		Replace_binary_single_byte(SA_TipFwAndHeader_L0_bin,140, ord(kmt_key_which_signs_tip_fw_L0[-1]) - ord('0'))        
		Replace_binary_single_byte(SkmtAndHeader_bin,      140, ord(kmt_key_which_signs_skmt[-1]) - ord('0'))
		Replace_binary_single_byte(TipFwAndHeader_L1_bin,  140, ord(skmt_key_which_signs_tip_fw_L1[-1]) - ord('0'))
		Replace_binary_single_byte(BootBlockAndHeader_bin, 140, ord(skmt_key_which_signs_bootblock[-1]) - ord('0'))
		Replace_binary_single_byte(BL31_AndHeader_bin,     140, ord(skmt_key_which_signs_BL31[-1]) - ord('0'))
		Replace_binary_single_byte(OpTeeAndHeader_bin,     140, ord(skmt_key_which_signs_OpTee[-1]) - ord('0'))
		Replace_binary_single_byte(UbootAndHeader_bin,     140, ord(skmt_key_which_signs_uboot[-1]) - ord('0'))
		
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
		
		Uboot_header_embed_pointers_to_all_fw()


		CRC32_binary(KmtAndHeader_bin           , 112    , 12     , KmtAndHeader_bin)
		CRC32_binary(TipFwAndHeader_L0_bin      , 112    , 12     , TipFwAndHeader_L0_bin)
		CRC32_binary(SA_TipFwAndHeader_L0_bin    , 112    , 12     , SA_TipFwAndHeader_L0_bin)        
		CRC32_binary(TipFwAndHeader_L1_bin      , 112    , 12     , TipFwAndHeader_L1_bin)
		
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
			Sign(TypeOfKey, pinCode, isPalladium, TypeOfKey_TIP, TypeOfKey_BMC)

	except (Exception) as e:
		print("\n GenerateImages.py: Error building binaries (%s)" % str(e))
		raise

	finally:
		os.chdir(currpath)

def Sign(TypeOfKey, pinCode, isPalladium, TypeOfKey_TIP=None, TypeOfKey_BMC=None):

	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	try:
		if TypeOfKey == "RemoteHSM":
			# Embed_external_sig(sig_der             , binfile                     , outputFile            , embed_signature)
			Embed_external_sig(KmtAndHeader_der      , KmtAndHeader_basic_bin      , KmtAndHeader_bin      , 16)
			Embed_external_sig(TipFwAndHeader_L0_der , TipFwAndHeader_L0_basic_bin , TipFwAndHeader_L0_bin , 16)
			Embed_external_sig(TipFwAndHeader_L0_der , SA_TipFwAndHeader_L0_basic_bin ,SA_TipFwAndHeader_L0_bin , 16)
			Embed_external_sig(SkmtAndHeader_der     , SkmtAndHeader_basic_bin     , SkmtAndHeader_bin     , 16)
			Embed_external_sig(TipFwAndHeader_L1_der , TipFwAndHeader_L1_basic_bin , TipFwAndHeader_L1_bin , 16)
			# BMC bootloaders not verified now. Use tip l1 signature for builds for now
			Embed_external_sig(BootBlockAndHeader_der, BootBlockAndHeader_basic_bin, BootBlockAndHeader_bin, 16)
			Embed_external_sig(BL31_AndHeader_der    , BL31_AndHeader_basic_bin    , BL31_AndHeader_bin    , 16)
			Embed_external_sig(OpTeeAndHeader_der    , OpTeeAndHeader_basic_bin    , OpTeeAndHeader_bin    , 16)
			Embed_external_sig(UbootAndHeader_der    , UbootAndHeader_basic_bin    , UbootAndHeader_bin    , 16)

		else:
			# Sign Images (and a secure  image)
			Sign_binary(KmtAndHeader_basic_bin,       112, eval(otp_key_which_signs_kmt),        16, KmtAndHeader_bin,       TypeOfKey_TIP, pinCode, eval("id_otp_key" + otp_key_which_signs_kmt[-1]))
			Sign_binary(TipFwAndHeader_L0_basic_bin,  112, eval(kmt_key_which_signs_tip_fw_L0),  16, TipFwAndHeader_L0_bin,  TypeOfKey_TIP, pinCode, eval("id_kmt_key" + kmt_key_which_signs_tip_fw_L0[-1]))
			Sign_binary(SA_TipFwAndHeader_L0_basic_bin,  112, eval(kmt_key_which_signs_tip_fw_L0),  16, SA_TipFwAndHeader_L0_bin,  TypeOfKey_TIP, pinCode, eval("id_kmt_key" + kmt_key_which_signs_tip_fw_L0[-1]))
			Sign_binary(SkmtAndHeader_basic_bin,      112, eval(kmt_key_which_signs_skmt),       16, SkmtAndHeader_bin,      TypeOfKey_TIP, pinCode, eval("id_kmt_key" + kmt_key_which_signs_skmt[-1]))
			Sign_binary(TipFwAndHeader_L1_basic_bin,  112, eval(skmt_key_which_signs_tip_fw_L1), 16, TipFwAndHeader_L1_bin,  TypeOfKey_TIP, pinCode, eval("id_skmt_key" + skmt_key_which_signs_tip_fw_L1[-1]))
			Sign_binary(BootBlockAndHeader_basic_bin, 112, eval(skmt_key_which_signs_bootblock), 16, BootBlockAndHeader_bin, TypeOfKey_BMC, pinCode, eval("id_skmt_key" + skmt_key_which_signs_bootblock[-1]))
			Sign_binary(UbootAndHeader_basic_bin,     112, eval(skmt_key_which_signs_uboot),     16, UbootAndHeader_bin,     TypeOfKey_BMC, pinCode, eval("id_skmt_key" + skmt_key_which_signs_uboot[-1]))
			Sign_binary(OpTeeAndHeader_basic_bin,     112, eval(skmt_key_which_signs_OpTee),     16, OpTeeAndHeader_bin,     TypeOfKey_BMC, pinCode, eval("id_skmt_key" + skmt_key_which_signs_OpTee[-1]))
			Sign_binary(BL31_AndHeader_basic_bin,     112, eval(skmt_key_which_signs_BL31),      16, BL31_AndHeader_bin,     TypeOfKey_BMC, pinCode, eval("id_skmt_key" + skmt_key_which_signs_BL31[-1]))

			Generate_binary(CpAndHeader_xml       , CpAndHeader_bin)
			
			# remove CRC
			# Note: secure image will hold both CRC and signature, so that same
			# bins will work both on basic and secure.
			
			# CRC32_remove(KmtAndHeader_bin          , 112    , 12     , KmtAndHeader_bin)
			# CRC32_remove(TipFwAndHeader_L0_bin     , 112    , 12     , TipFwAndHeader_L0_bin)
			# CRC32_remove(TipFwAndHeader_L1_bin     , 112    , 12     , TipFwAndHeader_L1_bin)

		MergeBinFilesAndPadAndPrint(isPalladium)
		# Move Secure images to Secure Directory
		MoveToFolder(isPalladium, secure_outputs_dir)
		# need to remove the no tip secure bin that was created in last operation of moving all from basic to secure
		os.remove(BootBlock_BL31_OpTee_uboot_secure_no_tip_bin)
	except (Exception) as e:
		print(("\n GenerateImages.py: Error building binaries (%s)" % str(e)))
		raise

	finally:
		os.chdir(currpath)
