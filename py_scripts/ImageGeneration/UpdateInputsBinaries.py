# SPDX-License-Identifier: GPL-2.0
#
# Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
#
# Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
#-------------------------------------------------------------------------

import sys
import os

from shutil import copyfile


inputs_dir = os.path.join("ImageGeneration", "inputs")
inputs_keys_dir = os.path.join("ImageGeneration", "inputs", "key_input")
bb_bin = "arbel_a35_bootblock.bin"
bb_bin_no_tip = "arbel_a35_bootblock_no_tip.bin"
bb_header_xml = "BootBlockAndHeader.xml"
bb_header_no_tip_xml = "BootBlockAndHeader_no_tip.xml"
uboot_bin = "u-boot.bin"
uboot_header_xml = "UbootHeader.xml"
tee_bin = "tee.bin"
bl31_bin = "bl31.bin"
image_file = "Image"
romfs_file = "romfs.img.gz"
dtb_file = "nuvoton-npcm845-evb.dtb"
uboot_env_file = "uboot_env.bin"
kmt_xml = "KmtAndHeader.xml"
Tip_FW_L0_file = "arbel_tip_fw_L0.bin"
Tip_FW_L1_file = "arbel_tip_fw_L1.bin"
tip_L0_xml = "TipFwAndHeader_L0.xml"
tip_L1_xml = "TipFwAndHeader_L1.xml"
CP_FW_file = "arbel_cp_fw.bin"
cp_xml = "CpFwAndHeader.xml"
fuse_xml = "arbel_fuse_map.xml"

def copy_files(src, dest, keys = 0):
	try:
		currpath = os.getcwd()
		dest_file = os.path.join(inputs_dir, dest)
		
		if keys == 1:
			dest_file = os.path.join(inputs_keys_dir, dest)

		if not os.path.isdir(inputs_dir):
			os.mkdir(inputs_dir)
			
		if not os.path.isdir(inputs_keys_dir):
			os.mkdir(inputs_keys_dir)

		if os.path.isfile(dest_file):
			os.remove(dest_file)

		print(("Copy %s to %s" % (src, dest_file)))
		copyfile(src, dest_file)
	except (Exception) as e:
		print("\n***************************************************")
		print("*******                                      ******")
		print("*******   ########     #      ###   #        ******")
		print("*******   #           # #      #    #        ******")
		print("*******   #          #   #     #    #        ******")
		print("*******   ########  #######    #    #        ******")
		print("*******   #         #     #    #    #        ******")
		print("*******   #         #     #    #    #        ******")
		print("*******   #         #     #   ###   #######  ******")
		print("*******                                      ******")
		print("***************************************************")
		print(("PWD:  %s" %(currpath)))
		print((" copy_files:         Copy %s to %s failed" % (src, dest_file) ))
		raise

def copy_bootblock_files(BootBlock, BBheader):

	copy_files(BootBlock, bb_bin)
	copy_files(BBheader, bb_header_xml)
	
def copy_bootblock_no_tip(BootBlock, BBheader):

	copy_files(BootBlock, bb_bin_no_tip)
	copy_files(BBheader, bb_header_no_tip_xml)

def copy_uboot_files(uboot, Ubootheader):

	copy_files(uboot, uboot_bin)
	copy_files(Ubootheader, uboot_header_xml)

def copy_tz_files(bl31, tee):

	copy_files(bl31, bl31_bin)
	copy_files(tee, tee_bin)


def copy_linux_files(Image, romfs, dtb):

	copy_files(Image, image_file)
	copy_files(romfs, romfs_file)
	copy_files(dtb, dtb_file)

def copy_uboot_env(uboot_env):

	copy_files(uboot_env, uboot_env_file)

def copy_kmt_files(kmtheader):

	copy_files(kmtheader, kmt_xml)

def copy_fuse_files(fuse):

	if os.path.isfile(fuse):
		copy_files(fuse, fuse_xml)
		
	else:
		print("   SKIP OTP FILE   ")
		return

	copy_files(fuse, fuse_xml)

def copy_tip_fw_files(tip_L0, tipheader_L0, tip_L1, tipheader_L1):

	copy_files(tip_L0, Tip_FW_L0_file)
	copy_files(tipheader_L0, tip_L0_xml)
	
	copy_files(tip_L1, Tip_FW_L1_file)
	copy_files(tipheader_L1, tip_L1_xml)

def copy_cp_fw_files(cp, cpheader):

	copy_files(cp, CP_FW_file)
	copy_files(cpheader, cp_xml)

def copy_default_keys():
	currpath = os.getcwd()	
	
	# if the fist key is there, doesn't touch the key_input folder
	single_key = os.path.join(inputs_dir, "key_input", "kmt_ecc_key_0_pub.der")
	if os.path.isfile(single_key):
		return

	src_dir = os.path.join("ImageGeneration", "keys", "openssl")
	dest_dir = os.path.join("ImageGeneration", "inputs", "key_input")
	
	if not os.path.isdir(dest_dir):
		os.mkdir(dest_dir)

	print(("Copy %s to %s" % (src_dir, dest_dir)))
	
	key_files = os.listdir(src_dir)
	
	for k in key_files:
		copy_files(os.path.join(src_dir, k), k)
		
