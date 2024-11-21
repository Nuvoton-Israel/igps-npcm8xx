# the following is Nuvoton recomendation on how to use the various key.
# Users are invited to edit key number in order to select different keys.

# Note: only key index can be changed, not key type (otp\kmt)


otp_key_which_signs_kmt          = "otp_key1"



kmt_key_which_signs_tip_fw_L0    = "kmt_key0"

kmt_key_which_signs_skmt         = "kmt_key1"



skmt_key_which_signs_tip_fw_L1   = "skmt_key0"

skmt_key_which_signs_bootblock   = "skmt_key1"

skmt_key_which_signs_BL31        = "skmt_key1"

skmt_key_which_signs_OpTee       = "skmt_key1"

skmt_key_which_signs_uboot       = "skmt_key1"

isECC = True

is_LMS_kmt = False
is_LMS_tip_fw_L0 = False
is_LMS_skmt = False
is_LMS_tip_fw_L1 = False

is_LMS_bootblock = False
is_LMS_BL31 = False
is_LMS_OpTee = False
is_LMS_uboot = False

# isLMS can be true, even when is_LMS_<image> is false. However if is_LMS_<image> is true, isLMS must be true as well , since it's not possible to verify with LMS key without creating the key (vice versa is allowed)
isLMS = False

lms_key_which_signs_kmt         = "otp_lms_key1"

lms_key_which_signs_tip_fw_L0   = "kmt_lms_key0"

lms_key_which_signs_skmt        = "kmt_lms_key1"

lms_key_which_signs_tip_fw_L1   = "skmt_lms_key5"

lms_key_which_signs_bootblock   = "skmt_lms_key6"

lms_key_which_signs_BL31        = "skmt_lms_key6"

lms_key_which_signs_OpTee       = "skmt_lms_key6"

lms_key_which_signs_uboot       = "skmt_lms_key6"

# to put manifests after L1: select 2048*1024.
# to put manifests at the end of flash: select 512*1024.
COMBO1_OFFSET  = 512*1024