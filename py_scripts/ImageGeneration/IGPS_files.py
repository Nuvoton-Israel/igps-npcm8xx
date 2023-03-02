# SPDX-License-Identifier: GPL-2.0
#
# Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
#
# Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
#-------------------------------------------------------------------------


import sys
import os

from shutil import move
from shutil import copyfile
from shutil import copy

inputs_dir = "inputs"
outputs_dir = "output_binaries"

input_key_dir                         = os.path.join(inputs_dir        , "key_input")
basic_outputs_dir                     = os.path.join(outputs_dir       , "Basic")
secure_outputs_dir                    = os.path.join(outputs_dir       , "Secure")


bb_bin            = os.path.join(inputs_dir        , "arbel_a35_bootblock.bin" )
uboot_bin         = os.path.join(inputs_dir        , "u-boot.bin"              )
tee_bin           = os.path.join(inputs_dir        , "tee.bin"                 )
bl31_bin          = os.path.join(inputs_dir        , "bl31.bin"                )
image_file        = os.path.join(inputs_dir        , "Image"                   )
romfs_file        = os.path.join(inputs_dir        , "romfs.img.gz"            )
dtb_file          = os.path.join(inputs_dir        , "nuvoton-npcm845-evb.dtb" )
uboot_env_file    = os.path.join(inputs_dir        , "uboot_env.bin"           )
Tip_FW_L0_file    = os.path.join(inputs_dir        , "arbel_tip_fw_L0.bin"     )
skmt_file         = os.path.join(inputs_dir        , "skmt_map.bin"            )
Tip_FW_L1_file    = os.path.join(inputs_dir        , "arbel_tip_fw_L1.bin"     )
CP_FW_file        = os.path.join(inputs_dir        , "arbel_cp_fw.bin"         )


BootBlockAndHeader_xml                = os.path.join(inputs_dir        , "BootBlockAndHeader.xml")
BootBlockAndHeader_bin                = os.path.join(outputs_dir       , "BootBlockAndHeader.bin")
BootBlockAndHeader_der                = os.path.join(outputs_dir       , "BootBlockAndHeader_sig.der")
BootBlockAndHeader_basic_bin          = os.path.join(basic_outputs_dir , "BootBlockAndHeader.bin")
BootBlockAndHeader_secure_bin         = os.path.join(secure_outputs_dir, "BootBlockAndHeader.bin")

BL31_AndHeader_xml                    = os.path.join(inputs_dir        , "BL31_AndHeader.xml")
BL31_AndHeader_bin                    = os.path.join(outputs_dir       , "BL31_AndHeader.bin")
BL31_AndHeader_der                    = os.path.join(outputs_dir       , "BL31_AndHeader_sig.der")
BL31_AndHeader_basic_bin              = os.path.join(basic_outputs_dir , "BL31_AndHeader.bin")
BL31_AndHeader_secure_bin             = os.path.join(secure_outputs_dir, "BL31_AndHeader.bin")

OpTeeAndHeader_xml                    = os.path.join(inputs_dir        , "OpTeeAndHeader.xml")
OpTeeAndHeader_bin                    = os.path.join(outputs_dir       , "OpTeeAndHeader.bin")
OpTeeAndHeader_der                    = os.path.join(outputs_dir       , "OpTeeAndHeader_sig.der")
OpTeeAndHeader_basic_bin              = os.path.join(basic_outputs_dir , "OpTeeAndHeader.bin")
OpTeeAndHeader_secure_bin             = os.path.join(secure_outputs_dir, "OpTeeAndHeader.bin")


UbootAndHeader_xml                    = os.path.join(inputs_dir        , "UbootHeader.xml")
UbootAndHeader_bin                    = os.path.join(outputs_dir       , "UbootAndHeader.bin")
UbootAndHeader_der                    = os.path.join(outputs_dir       , "UbootAndHeader_sig.der")
UbootAndHeader_basic_bin              = os.path.join(basic_outputs_dir , "UbootAndHeader.bin")
UbootAndHeader_secure_bin             = os.path.join(secure_outputs_dir, "UbootAndHeader.bin")

BootBlockAndUboot_basic_bin           = os.path.join(basic_outputs_dir , "BootBlockAndUboot.bin")
BootBlockAndUboot_secure_bin          = os.path.join(secure_outputs_dir, "BootBlockAndUboot.bin")


kmt_map_xml                           = os.path.join(inputs_dir        , "kmt_map.xml")
kmt_map_bin                           = os.path.join(inputs_dir        , "kmt_map.bin")

kmt_key0                              = os.path.join(input_key_dir        , "kmt_ecc_key_0.der")
id_kmt_key0 = "8"
kmt_key1                              = os.path.join(input_key_dir        , "kmt_ecc_key_1.der")
id_kmt_key1 = "9"

skmt_map_xml                           = os.path.join(inputs_dir        , "skmt_map.xml")
skmt_map_bin                           = os.path.join(inputs_dir        , "skmt_map.bin")

skmt_key0                              = os.path.join(input_key_dir        , "skmt_ecc_key_0.der")
id_skmt_key0 = "10"
skmt_key1                              = os.path.join(input_key_dir        , "skmt_ecc_key_1.der")
id_skmt_key1 = "11"
skmt_key2                              = os.path.join(input_key_dir        , "skmt_ecc_key_2.der")
id_skmt_key2 = "12"
skmt_key3                              = os.path.join(input_key_dir        , "skmt_ecc_key_3.der")
id_skmt_key3 = "13"
skmt_key4                              = os.path.join(input_key_dir        , "skmt_ecc_key_4.der")
id_skmt_key4 = "14"

rsa_key0                               = os.path.join(input_key_dir        , "rsa_key_0.der")
id_rsa_key0 = "15"

TipFwAndHeader_L0_xml                    = os.path.join(inputs_dir        , "TipFwAndHeader_L0.xml")
TipFwAndHeader_L0_bin                    = os.path.join(outputs_dir       , "TipFwAndHeader_L0.bin")
TipFwAndHeader_L0_der                    = os.path.join(outputs_dir       , "TipFwAndHeader_L0_sig.der")
TipFwAndHeader_L0_basic_bin              = os.path.join(basic_outputs_dir , "TipFwAndHeader_L0.bin")
TipFwAndHeader_L0_secure_bin             = os.path.join(secure_outputs_dir, "TipFwAndHeader_L0.bin")

TipFwAndHeader_L1_xml                    = os.path.join(inputs_dir        , "TipFwAndHeader_L1.xml")
TipFwAndHeader_L1_bin                    = os.path.join(outputs_dir       , "TipFwAndHeader_L1.bin")
TipFwAndHeader_L1_der                    = os.path.join(outputs_dir       , "TipFwAndHeader_L1_sig.der")
TipFwAndHeader_L1_basic_bin              = os.path.join(basic_outputs_dir , "TipFwAndHeader_L1.bin")
TipFwAndHeader_L1_secure_bin             = os.path.join(secure_outputs_dir, "TipFwAndHeader_L1.bin")

KmtAndHeader_xml                      = os.path.join(inputs_dir        , "KmtAndHeader.xml")
KmtAndHeader_bin                      = os.path.join(outputs_dir       , "KmtAndHeader.bin")
KmtAndHeader_der                      = os.path.join(outputs_dir       , "KmtAndHeader_sig.der")
KmtAndHeader_basic_bin                = os.path.join(basic_outputs_dir , "KmtAndHeader.bin")
KmtAndHeader_secure_bin               = os.path.join(secure_outputs_dir, "KmtAndHeader.bin")


SkmtAndHeader_xml                      = os.path.join(inputs_dir        , "SkmtAndHeader.xml")
SkmtAndHeader_bin                      = os.path.join(outputs_dir       , "SkmtAndHeader.bin")
SkmtAndHeader_der                      = os.path.join(outputs_dir       , "SkmtAndHeader_sig.der")
SkmtAndHeader_basic_bin                = os.path.join(basic_outputs_dir , "SkmtAndHeader.bin")
SkmtAndHeader_secure_bin               = os.path.join(secure_outputs_dir, "SkmtAndHeader.bin")

CpAndHeader_xml                       = os.path.join(inputs_dir        , "CpFwAndHeader.xml")
CpAndHeader_bin                       = os.path.join(outputs_dir       , "CpAndHeader.bin")
CpAndHeader_basic_bin                 = os.path.join(basic_outputs_dir , "CpAndHeader.bin")
CpAndHeader_secure_bin                = os.path.join(secure_outputs_dir , "CpAndHeader.bin")

tmp_bin                               = os.path.join(outputs_dir       , "tmp.bin")


image_bin                             = os.path.join(inputs_dir        , "Image")
romfs_bin                             = os.path.join(inputs_dir        , "romfs.img.gz")
dtb_bin                               = os.path.join(inputs_dir        , "nuvoton-npcm845-evb.dtb")

Kmt_TipFwL0_bin                       = os.path.join(outputs_dir       , "Kmt_TipFwL0.bin")
Kmt_TipFwL0_basic_bin                 = os.path.join(basic_outputs_dir , "Kmt_TipFwL0.bin")
Kmt_TipFwL0_secure_bin                = os.path.join(secure_outputs_dir, "Kmt_TipFwL0.bin")

Kmt_TipFwL0_Skmt_bin                         = os.path.join(outputs_dir       , "Kmt_TipFwL0_Skmt.bin")
Kmt_TipFwL0_Skmt_basic_bin                   = os.path.join(basic_outputs_dir , "Kmt_TipFwL0_Skmt.bin")
Kmt_TipFwL0_Skmt_secure_bin                  = os.path.join(secure_outputs_dir, "Kmt_TipFwL0_Skmt.bin")

Kmt_TipFwL0_Skmt_TipFwL1_bin                         = os.path.join(outputs_dir       , "Kmt_TipFwL0_Skmt_TipFwL1.bin")
Kmt_TipFwL0_Skmt_TipFwL1_basic_bin                   = os.path.join(basic_outputs_dir , "Kmt_TipFwL0_Skmt_TipFwL1.bin")
Kmt_TipFwL0_Skmt_TipFwL1_secure_bin                  = os.path.join(secure_outputs_dir, "Kmt_TipFwL0_Skmt_TipFwL1.bin")

Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_bin               = os.path.join(outputs_dir       , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_basic_bin         = os.path.join(basic_outputs_dir , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_secure_bin        = os.path.join(secure_outputs_dir, "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock.bin")

Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_bin               = os.path.join(outputs_dir       , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_basic_bin         = os.path.join(basic_outputs_dir , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_secure_bin        = os.path.join(secure_outputs_dir, "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31.bin")

Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_bin             = os.path.join(outputs_dir       , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_basic_bin         = os.path.join(basic_outputs_dir , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_secure_bin        = os.path.join(secure_outputs_dir, "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee.bin")



Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_bin         = os.path.join(outputs_dir       , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_uboot.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_basic_bin   = os.path.join(basic_outputs_dir , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_uboot.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_secure_bin  = os.path.join(secure_outputs_dir, "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_uboot.bin")

BootBlock_BL31_bin         = os.path.join(outputs_dir       , "BootBlock_BL31.bin")
BootBlock_BL31_basic_bin   = os.path.join(basic_outputs_dir , "BootBlock_BL31.bin")
BootBlock_BL31_secure_bin  = os.path.join(secure_outputs_dir, "BootBlock_BL31.bin")

BootBlock_BL31_OpTee_bin         = os.path.join(outputs_dir       , "BootBlock_BL31_Tee.bin")
BootBlock_BL31_OpTee_basic_bin   = os.path.join(basic_outputs_dir , "BootBlock_BL31_Tee.bin")
BootBlock_BL31_OpTee_secure_bin  = os.path.join(secure_outputs_dir, "BootBlock_BL31_Tee.bin")

BootBlock_BL31_OpTee_uboot_bin         = os.path.join(outputs_dir       , "BootBlock_BL31_Tee_uboot.bin")
BootBlock_BL31_OpTee_uboot_basic_bin   = os.path.join(basic_outputs_dir , "BootBlock_BL31_Tee_uboot.bin")
BootBlock_BL31_OpTee_uboot_secure_bin  = os.path.join(secure_outputs_dir, "BootBlock_BL31_Tee_uboot.bin")

Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_bin         = os.path.join(outputs_dir       , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_uboot.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_basic_bin   = os.path.join(basic_outputs_dir , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_uboot.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_secure_bin  = os.path.join(secure_outputs_dir, "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_uboot.bin")

Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_cp_bin         = os.path.join(outputs_dir       , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_uboot_cp.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_cp_basic_bin   = os.path.join(basic_outputs_dir , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_uboot_cp.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_cp_secure_bin  = os.path.join(secure_outputs_dir, "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_uboot_cp.bin")

Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_linux_bin          = os.path.join(outputs_dir       , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_uboot_linux.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_linux_basic_bin    = os.path.join(basic_outputs_dir , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_uboot_linux.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_linux_secure_bin   = os.path.join(secure_outputs_dir, "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_uboot_linux.bin")

Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_cp_linux_bin          = os.path.join(outputs_dir       , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_uboot_cp_linux.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_cp_linux_basic_bin    = os.path.join(basic_outputs_dir , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_uboot_cp_linux.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_cp_linux_secure_bin   = os.path.join(secure_outputs_dir, "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_Tee_uboot_cp_linux.bin")

Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_uboot_bin          = os.path.join(outputs_dir       , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_uboot.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_uboot_basic_bin    = os.path.join(basic_outputs_dir , "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_uboot.bin")
Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_uboot_secure_bin   = os.path.join(secure_outputs_dir, "Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_uboot.bin")


# note: the next files are used only for XIP mode (basic mode only), where KMT is not used
TipFw_BootBlock_bin                   = os.path.join(outputs_dir       , "TipFw_BootBlock.bin")
TipFw_BootBlock_basic_bin             = os.path.join(basic_outputs_dir , "TipFw_BootBlock.bin")
TipFw_BootBlock_uboot_bin             = os.path.join(outputs_dir       , "TipFw_BootBlock_uboot.bin")
TipFw_BootBlock_uboot_basic_bin       = os.path.join(basic_outputs_dir , "TipFw_BootBlock_uboot.bin")


arbel_fuse_map_xml                    = os.path.join(inputs_dir        , "arbel_fuse_map.xml")
arbel_fuse_map_bin                    = os.path.join(secure_outputs_dir, "arbel_fuse_map.bin")

otp_key0  = os.path.join(input_key_dir, "otp_ecc_key_0.der")
id_otp_key0 = "0"
otp_key1  = os.path.join(input_key_dir, "otp_ecc_key_1.der")
id_otp_key1 = "1"
otp_key2  = os.path.join(input_key_dir, "otp_ecc_key_2.der")
id_otp_key2 = "2"
otp_key3  = os.path.join(input_key_dir, "otp_ecc_key_3.der")
id_otp_key3 = "3"
otp_key4  = os.path.join(input_key_dir, "otp_ecc_key_4.der")
id_otp_key4 = "4"
otp_key5  = os.path.join(input_key_dir, "otp_ecc_key_5.der")
id_otp_key5 = "5"
otp_key6  = os.path.join(input_key_dir, "otp_ecc_key_6.der")
id_otp_key6 = "6"
otp_key7  = os.path.join(input_key_dir, "otp_ecc_key_7.der")
id_otp_key7 = "7"
otp_key8  = os.path.join(input_key_dir, "otp_ecc_key_8.der")
id_otp_key8 = "8"



from  .key_setting_edit_me import *

def CheckIfFileExistsAndMove(srcFile, toFolder):
	dstFile = os.path.join(toFolder, os.path.split(srcFile)[-1])
	
	if (os.path.isfile(srcFile) == False):
		print(("\033[91m" + "CheckIfFileExistsAndMove   Error: " +  srcFile + " file is missing\n\n" + "\033[97m"))
		return
	
	print(("     Copy " +  srcFile + " to " + toFolder))
	
	if os.path.isfile(dstFile):
		os.remove(dstFile)
	copy(srcFile, toFolder)
