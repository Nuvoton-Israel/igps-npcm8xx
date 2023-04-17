# SPDX-License-Identifier: GPL-2.0
#
# Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
#
# Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
#-------------------------------------------------------------------------

import os

from ImageGeneration.version_vars import *
from ImageGeneration.UpdateInputsBinaries import *
import ImageGeneration
from ImageGeneration.BinaryGenerator import * 



versions_dir = os.path.join("ImageGeneration", "versions")
ref_dir = os.path.join("ImageGeneration", "references")

kmt_xml_source = os.path.join(ref_dir, "KmtAndHeader_Z1.xml")

fuse_xml_source = os.path.join(ref_dir, "arbel_fuse_map_Z1.xml")

TipFW_L0_bin_source = os.path.join(versions_dir, arbel_tip_fw_L0)
TipFW_L0_xml_source = os.path.join(ref_dir, "TipFwAndHeader_L0_Z1.xml")

TipFW_L1_bin_source = os.path.join(versions_dir, arbel_tip_fw_L1)
TipFW_L1_xml_source = os.path.join(ref_dir, "TipFwAndHeader_L1_Z1.xml")

CpFW_bin_source = os.path.join(versions_dir, "arbel_cp_fw.bin")  # TODO: change after cp fw first version

#todo:
CpFW_xml_source = os.path.join(ref_dir, "CpFwAndHeader.xml")


BootBlock_bin_source = os.path.join(versions_dir, arbel_a35_bootblock)
BBheader_xml_source = os.path.join(ref_dir, "BootBlockAndHeader_Z1_SVB.xml")

uboot_bin_source = os.path.join(versions_dir, arbel_uboot)

Ubootheader_xml_source = os.path.join(ref_dir, "UbootHeader_Z1.xml")

tee_bin_source = os.path.join(versions_dir, arbel_tee)
bl31_bin_source = os.path.join(versions_dir, arbel_bl31)


linux_image_source = os.path.join(versions_dir, linux_image)
linux_fs_source = os.path.join(versions_dir, linux_romfs)
linux_dtb_source = os.path.join(versions_dir, linux_dtb_evb)

uboot_env_source = os.path.join(ref_dir, "uboot_env_svb.bin")


try:
	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	print("--------------------------------------")
	print("Updating input binaries for  Arbel PD")
	print("--------------------------------------")

	if not os.path.isdir(ref_dir):
		os.mkdir(ref_dir)

	ImageGeneration.UpdateInputsBinaries.copy_fuse_files(fuse_xml_source)
	ImageGeneration.UpdateInputsBinaries.copy_kmt_files(kmt_xml_source)
	ImageGeneration.UpdateInputsBinaries.copy_tip_fw_files(TipFW_L0_bin_source, TipFW_L0_xml_source, TipFW_L1_bin_source, TipFW_L1_xml_source)
	ImageGeneration.UpdateInputsBinaries.copy_cp_fw_files(CpFW_bin_source, CpFW_xml_source)
	ImageGeneration.UpdateInputsBinaries.copy_bootblock_files(BootBlock_bin_source, BBheader_xml_source)
	ImageGeneration.UpdateInputsBinaries.copy_uboot_files(uboot_bin_source, Ubootheader_xml_source)
	ImageGeneration.UpdateInputsBinaries.copy_tz_files(bl31_bin_source, tee_bin_source)
	ImageGeneration.UpdateInputsBinaries.copy_linux_files(linux_image_source, linux_fs_source, linux_dtb_source)
	ImageGeneration.UpdateInputsBinaries.copy_default_keys()

	print("---------------------------------------------")
	print("Binaries for Arbel PD are ready in 'inputs'")
	print("---------------------------------------------")

except (IOError) as e:
	print(("Error Updating input Binaries (%s)" % (e.strerror)))
except:
	print("Error Updating input Binaries")
finally:
	os.chdir(currpath)

