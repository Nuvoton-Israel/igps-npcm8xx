# SPDX-License-Identifier: GPL-2.0
#
# Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
#
# Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
#-------------------------------------------------------------------------

from ImageGeneration.IGPS_files import *

def copy_files(src, dest, keys = 0):
	try:
		currpath = os.getcwd()
		dest_file = os.path.join("ImageGeneration", inputs_dir, dest)
		
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
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
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

	copy_files(BootBlock, filename_bb_bin)
	copy_files(BBheader, filename_bb_header_xml)
	
def copy_bootblock_no_tip(BootBlock, BBheader):

	copy_files(BootBlock, filename_bb_bin_no_tip)
	copy_files(BBheader, filename_bb_header_no_tip_xml)

def copy_uboot_files(uboot, Ubootheader):

	copy_files(uboot, filename_uboot_bin)
	copy_files(Ubootheader, filename_uboot_header_xml)

def copy_tz_files(bl31, bl31header, tee, tee_header):

	copy_files(bl31, filename_bl31_bin)
	copy_files(bl31header, filename_bl31_xml)
	copy_files(tee, filename_tee_bin)
	copy_files(tee_header, filename_tee_xml)


def copy_linux_files(Image, romfs, dtb):

	copy_files(Image, filename_image_file)
	copy_files(romfs, filename_romfs_file)
	copy_files(dtb, filename_dtb_file)

def copy_uboot_env(uboot_env):

	copy_files(uboot_env, filename_uboot_env_file)

def copy_kmt_files(kmtheader, skmtheader):

	copy_files(kmtheader, filename_kmt_xml)
	copy_files(skmtheader, filename_skmt_xml)

def copy_fuse_files(fuse):

	if os.path.isfile(fuse):
		copy_files(fuse, filename_fuse_xml)
		
	else:
		print("   SKIP OTP FILE   ")
		return


def copy_tip_fw_files(tip_L0, tipheader_L0, sa_tip_L0, sa_tip_xml, tip_L1, tipheader_L1, L0_UT_xml):

	copy_files(tip_L0, filename_Tip_FW_L0_file)
	copy_files(tipheader_L0, filename_tip_L0_xml)
	
	copy_files(L0_UT_xml, filename_tip_L0_UT_xml)

	copy_files(sa_tip_L0, filename_SA_Tip_FW_L0_file)
	copy_files(sa_tip_xml, filename_sa_xml)

	copy_files(tip_L1, filename_Tip_FW_L1_file)
	copy_files(tipheader_L1, filename_tip_L1_xml)

def copy_cp_fw_files(cp, cpheader):

	copy_files(cp, filename_CP_FW_file)
	copy_files(cpheader, filename_cp_xml)

def copy_default_keys():
	currpath = os.getcwd()

	src_dir = os.path.join("ImageGeneration", "keys", "openssl")
	dest_dir = os.path.join("ImageGeneration", "inputs", "key_input")
	
	if not os.path.isdir(dest_dir):
		os.mkdir(dest_dir)

	print(("Copy %s to %s" % (src_dir, dest_dir)))
	
	key_files = os.listdir(src_dir)
	
	for k in key_files:
		copyfile(os.path.join(src_dir, k), os.path.join(dest_dir, k))
		
