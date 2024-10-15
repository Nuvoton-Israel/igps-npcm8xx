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
tmp_outputs_dir                       = os.path.join(outputs_dir       , "tmp")
inputs_keys_dir                       = os.path.join("ImageGeneration", "inputs", "key_input")

# filenames used for inputs directory:
filename_bb_bin = "arbel_a35_bootblock.bin"
filename_bb_bin_no_tip = "arbel_a35_bootblock_no_tip.bin"
filename_bb_header_xml = "BootBlockAndHeader.xml"
filename_bb_header_no_tip_xml = "BootBlockAndHeader_no_tip.xml"
filename_uboot_bin = "u-boot.bin"
filename_uboot_header_xml = "UbootHeader.xml"
filename_tee_bin = "tee.bin"
filename_bl31_bin = "bl31.bin"
filename_image_file = "Image"
filename_romfs_file = "romfs.img.gz"
filename_dtb_file = "nuvoton-npcm845-evb.dtb"
filename_uboot_env_file = "uboot_env.bin"
filename_kmt_xml = "KmtAndHeader.xml"
filename_Tip_FW_L0_file = "arbel_tip_fw_L0.bin"
filename_Tip_FW_L0_UT_file = "arbel_tip_fw_L0_UT.bin"
filename_SA_Tip_FW_L0_file = "sa_arbel_tip_fw_L0.bin"
filename_Tip_FW_L1_file = "arbel_tip_fw_L1.bin"
filename_tip_L0_xml = "TipFwAndHeader_L0.xml"
filename_tip_L0_UT_xml = "TipFwAndHeader_L0_UT.xml"
filename_tip_L1_xml = "TipFwAndHeader_L1.xml"
filename_CP_FW_file = "arbel_cp_fw.bin"
filename_cp_xml = "CpFwAndHeader.xml"
filename_fuse_xml = "arbel_fuse_map.xml"
filename_bl31_xml = "BL31_AndHeader.xml"
filename_tee_xml = "OpTeeAndHeader.xml"
filename_skmt_xml = "SkmtAndHeader.xml"
filename_kmt_bin = "kmt_map.bin"
filename_skmt_bin = "skmt_map.bin"
filename_sa_xml = "SA_TipFwAndHeader_L0.xml"
filename_sa_bin = "SA_TipFwAndHeader_L0.bin"

bb_bin               = os.path.join(inputs_dir, filename_bb_bin               )
bb_bin_no_tip        = os.path.join(inputs_dir, filename_bb_bin_no_tip        )
bb_header_xml        = os.path.join(inputs_dir, filename_bb_header_xml        )
bb_header_no_tip_xml = os.path.join(inputs_dir, filename_bb_header_no_tip_xml )
uboot_bin            = os.path.join(inputs_dir, filename_uboot_bin            )
uboot_header_xml     = os.path.join(inputs_dir, filename_uboot_header_xml     )
tee_bin              = os.path.join(inputs_dir, filename_tee_bin              )
bl31_bin             = os.path.join(inputs_dir, filename_bl31_bin             )
image_bin            = os.path.join(inputs_dir, filename_image_file           )
romfs_bin            = os.path.join(inputs_dir, filename_romfs_file           )
dtb_bin              = os.path.join(inputs_dir, filename_dtb_file             )
uboot_env_file       = os.path.join(inputs_dir, filename_uboot_env_file       )
kmt_xml              = os.path.join(inputs_dir, filename_kmt_xml              )
Tip_FW_L0_bin        = os.path.join(inputs_dir, filename_Tip_FW_L0_file       )
Tip_FW_L0_UT_bin     = os.path.join(inputs_dir, filename_Tip_FW_L0_UT_file       )
SA_Tip_FW_L0_bin     = os.path.join(inputs_dir, filename_SA_Tip_FW_L0_file    )
Tip_FW_L1_bin        = os.path.join(inputs_dir, filename_Tip_FW_L1_file       )
tip_L0_xml           = os.path.join(inputs_dir, filename_tip_L0_xml           )
tip_L0_UT_xml        = os.path.join(inputs_dir, filename_tip_L0_UT_xml )
tip_L1_xml           = os.path.join(inputs_dir, filename_tip_L1_xml           )
CP_FW_bin            = os.path.join(inputs_dir, filename_CP_FW_file           )
cp_xml               = os.path.join(inputs_dir, filename_cp_xml               )
fuse_xml             = os.path.join(inputs_dir, filename_fuse_xml             )
bl31_xml             = os.path.join(inputs_dir, filename_bl31_xml             )
tee_xml              = os.path.join(inputs_dir, filename_tee_xml              )
skmt_xml             = os.path.join(inputs_dir, filename_skmt_xml             )
skmt_bin             = os.path.join(inputs_dir, filename_skmt_bin             )
sa_xml               = os.path.join(inputs_dir, filename_sa_xml               )

bb_tmp_bin               = os.path.join(tmp_outputs_dir, filename_bb_bin               )
bb_tmp_bin_no_tip        = os.path.join(tmp_outputs_dir, filename_bb_bin_no_tip        )
uboot_tmp_bin            = os.path.join(tmp_outputs_dir, filename_uboot_bin            )
tee_tmp_bin              = os.path.join(tmp_outputs_dir, filename_tee_bin              )
bl31_tmp_bin             = os.path.join(tmp_outputs_dir, filename_bl31_bin             )
image_tmp_bin            = os.path.join(tmp_outputs_dir, filename_image_file           )
romfs_tmp_bin            = os.path.join(tmp_outputs_dir, filename_romfs_file           )
dtb_tmp_bin              = os.path.join(tmp_outputs_dir, filename_dtb_file             )
uboot_env_file           = os.path.join(tmp_outputs_dir, filename_uboot_env_file       )
Tip_FW_L0_tmp_bin        = os.path.join(tmp_outputs_dir, filename_Tip_FW_L0_file       )
Tip_FW_L0_UT_tmp_bin     = os.path.join(tmp_outputs_dir, filename_Tip_FW_L0_UT_file    )
SA_Tip_FW_L0_tmp_bin     = os.path.join(tmp_outputs_dir, filename_SA_Tip_FW_L0_file    )
Tip_FW_L1_tmp_bin        = os.path.join(tmp_outputs_dir, filename_Tip_FW_L1_file       )
CP_FW_tmp_bin            = os.path.join(tmp_outputs_dir, filename_CP_FW_file           )
skmt_map_tmp_bin         = os.path.join(tmp_outputs_dir, filename_skmt_bin             )
kmt_map_tmp_bin          = os.path.join(tmp_outputs_dir, filename_kmt_bin              )

BootBlockAndHeader_xml                = os.path.join(inputs_dir        , "BootBlockAndHeader.xml")
BootBlockAndHeader_bin                = os.path.join(outputs_dir       , "BootBlockAndHeader.bin")
BootBlockAndHeader_der                = os.path.join(outputs_dir       , "BootBlockAndHeader_sig.der")
BootBlockAndHeader_basic_bin          = os.path.join(basic_outputs_dir , "BootBlockAndHeader.bin")
BootBlockAndHeader_secure_bin         = os.path.join(secure_outputs_dir, "BootBlockAndHeader.bin")

BootBlockAndHeader_no_tip_xml         = os.path.join(inputs_dir        , "BootBlockAndHeader_no_tip.xml")
BootBlockAndHeader_no_tip_bin         = os.path.join(outputs_dir       , "BootBlockAndHeader_no_tip.bin")
BootBlockAndHeader_no_tip_basic_bin   = os.path.join(basic_outputs_dir , "BootBlockAndHeader_no_tip.bin")
BootBlockAndHeader_no_tip_secure_bin  = os.path.join(secure_outputs_dir, "BootBlockAndHeader_no_tip.bin")

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

kmt_map_xml                           = os.path.join(inputs_dir        , "kmt_map.xml")
kmt_map_lms_xml                       = os.path.join(inputs_dir        , "kmt_map_lms.xml")
kmt_map_bin                           = os.path.join(tmp_outputs_dir,    "kmt_map.bin")

skmt_map_xml                           = os.path.join(inputs_dir       , "skmt_map.xml")
skmt_map_lms_xml                       = os.path.join(inputs_dir       , "skmt_map_lms.xml")
skmt_map_bin                           = os.path.join(tmp_outputs_dir,   "skmt_map.bin")

rsa_key0                               = os.path.join(input_key_dir    , "rsa_key_0.der")
id_rsa_key0 = "15"

TipFwAndHeader_L0_xml                    = os.path.join(inputs_dir        , "TipFwAndHeader_L0.xml")
TipFwAndHeader_L0_bin                    = os.path.join(outputs_dir       , "TipFwAndHeader_L0.bin")
TipFwAndHeader_L0_der                    = os.path.join(outputs_dir       , "TipFwAndHeader_L0_sig.der")
TipFwAndHeader_L0_basic_bin              = os.path.join(basic_outputs_dir , "TipFwAndHeader_L0.bin")
TipFwAndHeader_L0_secure_bin             = os.path.join(secure_outputs_dir, "TipFwAndHeader_L0.bin")

TipFwAndHeader_L0_UT_xml                    = os.path.join(inputs_dir        , "TipFwAndHeader_L0_UT.xml")
TipFwAndHeader_L0_UT_bin                    = os.path.join(outputs_dir       , "TipFwAndHeader_L0_UT.bin")
TipFwAndHeader_L0_UT_der                    = os.path.join(outputs_dir       , "TipFwAndHeader_L0_UT_sig.der")
TipFwAndHeader_L0_UT_basic_bin              = os.path.join(basic_outputs_dir , "TipFwAndHeader_L0_UT.bin")
TipFwAndHeader_L0_UT_secure_bin             = os.path.join(secure_outputs_dir, "TipFwAndHeader_L0_UT.bin")


SA_TipFwAndHeader_L0_bin                  = os.path.join(outputs_dir        , "SA_TipFwAndHeader_L0.bin")
SA_TipFwAndHeader_L0_xml                  = os.path.join(inputs_dir         , "SA_TipFwAndHeader_L0.xml")
SA_TipFwAndHeader_L0_basic_bin            = os.path.join(basic_outputs_dir  , "SA_TipFwAndHeader_L0.bin")
SA_TipFwAndHeader_L0_secure_bin           = os.path.join(secure_outputs_dir , "SA_TipFwAndHeader_L0.bin")

image_no_tip_SA_bin                       = os.path.join(outputs_dir        , "image_no_tip_SA.bin")
image_no_tip_SA_basic_bin                 = os.path.join(basic_outputs_dir  , "image_no_tip_SA.bin")
image_no_tip_SA_secure_bin                = os.path.join(secure_outputs_dir , "image_no_tip_SA.bin")

TipFwAndHeader_L1_xml                    = os.path.join(inputs_dir        , "TipFwAndHeader_L1.xml")
TipFwAndHeader_L1_bin                    = os.path.join(outputs_dir       , "TipFwAndHeader_L1.bin")
TipFwAndHeader_L1_der                    = os.path.join(outputs_dir       , "TipFwAndHeader_L1_sig.der")
TipFwAndHeader_L1_basic_bin              = os.path.join(basic_outputs_dir , "TipFwAndHeader_L1.bin")
TipFwAndHeader_L1_secure_bin             = os.path.join(secure_outputs_dir, "TipFwAndHeader_L1.bin")

KmtAndHeader_xml                      = os.path.join(inputs_dir        , "KmtAndHeader.xml")
Kmt_tmp_bin                           = os.path.join(tmp_outputs_dir   , "kmt_map_bin.bin")
KmtAndHeader_bin                      = os.path.join(outputs_dir       , "KmtAndHeader.bin")
KmtAndHeader_der                      = os.path.join(outputs_dir       , "KmtAndHeader_sig.der")
KmtAndHeader_basic_bin                = os.path.join(basic_outputs_dir , "KmtAndHeader.bin")
KmtAndHeader_secure_bin               = os.path.join(secure_outputs_dir, "KmtAndHeader.bin")

SkmtAndHeader_xml                      = os.path.join(inputs_dir        , "SkmtAndHeader.xml")
Skmt_tmp_bin                           = os.path.join(tmp_outputs_dir   , "skmt_map_bin.bin")
SkmtAndHeader_bin                      = os.path.join(outputs_dir       , "SkmtAndHeader.bin")
SkmtAndHeader_der                      = os.path.join(outputs_dir       , "SkmtAndHeader_sig.der")
SkmtAndHeader_basic_bin                = os.path.join(basic_outputs_dir , "SkmtAndHeader.bin")
SkmtAndHeader_secure_bin               = os.path.join(secure_outputs_dir, "SkmtAndHeader.bin")

CpAndHeader_xml                       = os.path.join(inputs_dir        , "CpFwAndHeader.xml")
CpAndHeader_bin                       = os.path.join(outputs_dir       , "CpAndHeader.bin")
CpAndHeader_basic_bin                 = os.path.join(basic_outputs_dir , "CpAndHeader.bin")
CpAndHeader_secure_bin                = os.path.join(secure_outputs_dir , "CpAndHeader.bin")

tmp_bin                               = os.path.join(outputs_dir       , "tmp.bin")



Kmt_TipFwL0_bin                       = os.path.join(outputs_dir       , "Kmt_TipFwL0.bin")
Kmt_TipFwL0_basic_bin                 = os.path.join(basic_outputs_dir , "Kmt_TipFwL0.bin")
Kmt_TipFwL0_secure_bin                = os.path.join(secure_outputs_dir, "Kmt_TipFwL0.bin")


Kmt_TipFwL0_UT_bin                       = os.path.join(outputs_dir       , "Kmt_TipFwL0_UT.bin")
Kmt_TipFwL0_UT_basic_bin                 = os.path.join(basic_outputs_dir , "Kmt_TipFwL0_UT.bin")
Kmt_TipFwL0_UT_secure_bin                = os.path.join(secure_outputs_dir, "Kmt_TipFwL0_UT.bin")


SA_Kmt_TipFwL0_bin                     = os.path.join(outputs_dir       , "SA_Kmt_TipFwL0.bin")
SA_Kmt_TipFwL0_basic_bin               = os.path.join(basic_outputs_dir , "SA_Kmt_TipFwL0.bin")
SA_Kmt_TipFwL0_secure_bin              = os.path.join(secure_outputs_dir, "SA_Kmt_TipFwL0.bin")

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

BootBlock_BL31_no_tip_bin         = os.path.join(outputs_dir       , "BootBlock_BL31_no_tip.bin")
BootBlock_BL31_basic_no_tip_bin   = os.path.join(basic_outputs_dir , "BootBlock_BL31_no_tip.bin")

BootBlock_BL31_OpTee_no_tip_bin         = os.path.join(outputs_dir       , "BootBlock_BL31_Tee_no_tip.bin")
BootBlock_BL31_OpTee_basic_no_tip_bin   = os.path.join(basic_outputs_dir , "BootBlock_BL31_Tee_no_tip.bin")

BootBlock_BL31_OpTee_uboot_no_tip_bin         = os.path.join(outputs_dir       , "image_no_tip.bin")
BootBlock_BL31_OpTee_uboot_basic_no_tip_bin   = os.path.join(basic_outputs_dir , "image_no_tip.bin")
BootBlock_BL31_OpTee_uboot_secure_no_tip_bin = os.path.join(secure_outputs_dir , "image_no_tip.bin")

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
id_otp_key8 = "15"

otp_lms_key1  = os.path.join(input_key_dir, "otp_lms_key_1.bin")
id_otp_key1 = "22"

otp_lms_key2  = os.path.join(input_key_dir, "otp_lms_key_1.bin")
id_otp_key2 = "23"

kmt_key0                              = os.path.join(input_key_dir        , "kmt_ecc_key_0.der")
id_kmt_key0 = "8"
kmt_key1                              = os.path.join(input_key_dir        , "kmt_ecc_key_1.der")
id_kmt_key1 = "9"

kmt_lms_key2                              = os.path.join(input_key_dir        , "kmt_lms_key_2.bin")
id_lms_kmt_key0 = "20"
kmt_lms_key3                             = os.path.join(input_key_dir        , "kmt_lms_key_3.bin")
id_lms_kmt_key1 = "21"

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

skmt_lms_key5                           = os.path.join(input_key_dir    , "skmt_lms_key_5.bin")
id_skmt_lms_key0 = "15"

skmt_lms_key6                           = os.path.join(input_key_dir    , "skmt_lms_key_6.bin")
id_skmt_lms_key1 = "16"


# versions_dir                          = os.path.join("ImageGeneration", "versions")
chip_xml                = os.path.join("versions", "npcm8xx.chip")
registers_L1            = os.path.join("inputs", "registers", "registers_tip_fw_L1.csv")
registers_bootblock     = os.path.join("inputs", "registers", "registers_bootblock.csv")
registers_bl31          = os.path.join("inputs", "registers", "registers_bl31.csv")
registers_optee         = os.path.join("inputs", "registers", "registers_optee.csv")
registers_uboot         = os.path.join("inputs", "registers", "registers_uboot.csv")

registers_outputs_dir     = os.path.join(outputs_dir, "regs")

bin_registers_L1        = os.path.join("output_binaries", "regs", "registers_tip_fw_L1.bin")
bin_registers_bootblock = os.path.join("output_binaries", "regs", "registers_bootblock.bin")
bin_registers_bl31      = os.path.join("output_binaries", "regs", "registers_bl31.bin")
bin_registers_optee     = os.path.join("output_binaries", "regs", "registers_optee.bin")
bin_registers_uboot     = os.path.join("output_binaries", "regs", "registers_uboot.bin")


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
