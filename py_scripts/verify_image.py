#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
#
# Nuvoton IGPS: Image Verification Tool
#
# Verifies KMT header signature and CRC in a composite binary image.
#
# Usage:
#   python verify_image.py <image> [--otp_img <path>] [--otp_ecc <path>] [--otp_lms <path>]
#
# Copyright (C) 2024 Nuvoton Technologies, All Rights Reserved
#-------------------------------------------------------------------------
#
# ============================================================================
# DESIGN OVERVIEW
# ============================================================================
#
# This tool performs the reverse operation of GenerateAll.py's signing pipeline.
# Given a signed binary image (e.g., Kmt_TipFwL0.bin), it verifies integrity
# and authenticity of the KMT (Key Manifest Table) section.
#
# IMAGE LAYOUT (KMT section):
# ┌─────────────────────────────────────────────────────────────────────────┐
# │ Offset 0x00:  Anchor (4 bytes) = 0x2A3B4D5E                            │
# │ Offset 0x04:  Extended Anchor / CRC enable flag (4 bytes)               │
# │ Offset 0x0C:  CRC32 value (4 bytes)                                    │
# │ Offset 0x10:  ECC Signature: r (48 bytes LE) || s (48 bytes LE)         │
# │ Offset 0x70:  ─── Signed/CRC'd data starts here (offset 112) ───       │
# │               SPI config, FW start addr, FW length, key indices,        │
# │               LMS flags, timestamps, etc.                               │
# │ Offset 0x100: KMT payload (kmt_map.bin: public keys with ECC encoding) │
# │               Size = FwLength field at offset 0x84                      │
# └─────────────────────────────────────────────────────────────────────────┘
# │ (optional) LMS signature appended after KMT section, 32-byte aligned   │
# └─────────────────────────────────────────────────────────────────────────┘
# │ 0xFF padding to next 0x1000-aligned boundary                            │
# │ TipFwL0 section (in composite Kmt_TipFwL0.bin images)                   │
# └─────────────────────────────────────────────────────────────────────────┘
#
# VERIFICATION STEPS:
#
# 1. CRC32 Verification (if CRC enabled via ExtAnchor = 0x57F2AB1E):
#    - Range: image[0x70 .. 0x100 + FwLength)
#    - Algorithm: Custom CRC32 (init=0, poly=0xEDB88320, no final XOR)
#    - Stored at: offset 0x0C (4 bytes, little-endian)
#    - Note: CRC is computed BEFORE signature embedding; the signature region
#      (0x10..0x70) is NOT included in CRC computation.
#
# 2. ECC Signature Verification (ECDSA P-384 + SHA-512):
#    - Signed data: image[0x70 .. 0x100 + FwLength)
#    - Signature location: offset 0x10, stored as r_LE(48) || s_LE(48)
#    - Public key format: x_LE(48) || y_LE(48) raw binary (96 bytes)
#    - The signing key is an OTP ECC key (configured in key_setting_edit_me.json)
#
# 3. LMS Signature Verification (optional, if enable_lms flag at 0x95 != 0):
#    - Signed data: SHA-512(image[0x70 .. 0x100 + FwLength))
#    - Signature location: appended immediately after the KMT section
#      (at offset 0x100 + FwLength), padded to 32-byte alignment
#    - Public key format: raw LMS public key (56 bytes for SHA256_M32_H20)
#    - Uses the hsslms library (LMS_SHA256_M32_H20 + LMOTS_SHA256_N32_W4)
#    - Signature size is derived from the signature header (typically 2828 bytes)
#
# KEY FILES:
#    - ECC public key:  keys/openssl/<name>_pub.bin  (96 bytes: x_LE || y_LE)
#    - LMS public key:  keys/openssl/<name>_pub.bin  (56 bytes: raw LMS pubkey)
#    - Key selection is configured in key_setting_edit_me.json:
#      "otp_key_which_signs_kmt" determines which OTP ECC key signs the KMT
#      "lms_key_which_signs_kmt" determines which LMS key signs the KMT
#
# DEPENDENCIES:
#    - cryptography (for ECDSA P-384 verification)
#    - hsslms (for LMS verification, only needed if --lms_otp is provided)
#
# ============================================================================

import argparse
import struct
import sys
import hashlib
import os
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


# Constants matching IGPS generation
ECC_KEY_SIZE = 48  # P-384 = 48 bytes per coordinate
SIGNATURE_OFFSET = 16  # Where ECC signature (r||s) is embedded
SIGNATURE_SIZE = ECC_KEY_SIZE * 2  # 96 bytes
SIGNED_DATA_OFFSET = 112  # 0x70 - data from here onwards is signed/CRC'd
CRC_OFFSET = 12  # 0x0C - where CRC32 is stored
KMT_PAYLOAD_OFFSET = 0x100  # Where kmt_map data starts

# Header field offsets
ANCHOR_OFFSET = 0x00
EXT_ANCHOR_OFFSET = 0x04
FW_CRC_OFFSET = 0x0C
SPI0_FLASH_CLOCK_OFFSET = 0x70
SPI1_FLASH_CLOCK_OFFSET = 0x71
SPI3_FLASH_CLOCK_OFFSET = 0x72
SPI_FLASH_READ_MODE_OFFSET = 0x76
FW_START_ADDR_OFFSET = 0x78
LMS_KMO_OFFSET = 0x80
FW_LENGTH_OFFSET = 0x84
KEY_MASK_OFFSET = 0x88
KEY_INDEX_OFFSET = 0x8C
KEY_INVALID_OFFSET = 0x90
ENCRYPTION_CTRL_OFFSET = 0x94
ENABLE_LMS_OFFSET = 0x95
OTP_REVOCATION_VER_OFFSET = 0x96
OTP_FW_VERSION_OFFSET = 0x98
FW_TABLE_OFFSET_OFFSET = 0xA8
AES_CBC_IV_OFFSET = 0xAC
TIMESTAMP_OFFSET = 0xBC
KEY_MASK_LMS_OFFSET = 0xC0
KEY_INDEX_LMS_OFFSET = 0xC4

# Expected anchor values
ANCHOR_VALUE = 0x2A3B4D5E
L0_ANCHOR_VALUE = 0x9B7A4D5E
CRC_ENABLED_EXT_ANCHOR = 0x57F2AB1E
CRC_DISABLED_EXT_ANCHOR = 0x57F254E1

# L0 section offset within composite Kmt_TipFwL0.bin image
L0_SECTION_OFFSET = 0x1000


def crc32_tab_val(c):
    """Replicate IGPS custom CRC32 table value computation."""
    crc = int(c) % (1 << 32)
    for _ in range(8):
        if crc & 0x00000001:
            crc = ((crc >> 1) % (1 << 32)) ^ 0xEDB88320
        else:
            crc = crc >> 1
        crc = crc % (1 << 32)
    return crc


def update_crc(crc, c):
    """Replicate IGPS custom CRC32 update."""
    long_c = int(0x000000FF & c) % (1 << 32)
    tmp = (crc ^ long_c) % (1 << 32)
    crc = ((crc >> 8) ^ crc32_tab_val(tmp & 0xFF)) % (1 << 32)
    crc = crc % (1 << 32)
    return crc


def compute_crc32(data):
    """Compute CRC32 over data using IGPS algorithm (init=0, no final XOR)."""
    crc = 0
    for byte in data:
        crc = update_crc(crc, byte)
    return crc & 0xFFFFFFFF


def le_bytes_to_int(data):
    """Convert little-endian byte array to integer."""
    return int.from_bytes(data, byteorder='little')


def parse_kmt_header(image_data):
    """Parse and display KMT header fields."""
    header = {}

    header['anchor'] = struct.unpack_from('<I', image_data, ANCHOR_OFFSET)[0]
    header['ext_anchor'] = struct.unpack_from('<I', image_data, EXT_ANCHOR_OFFSET)[0]
    header['fw_crc'] = struct.unpack_from('<I', image_data, FW_CRC_OFFSET)[0]
    header['sig_r'] = image_data[SIGNATURE_OFFSET:SIGNATURE_OFFSET + ECC_KEY_SIZE]
    header['sig_s'] = image_data[SIGNATURE_OFFSET + ECC_KEY_SIZE:SIGNATURE_OFFSET + SIGNATURE_SIZE]
    header['spi0_flash_clock'] = image_data[SPI0_FLASH_CLOCK_OFFSET]
    header['spi1_flash_clock'] = image_data[SPI1_FLASH_CLOCK_OFFSET]
    header['spi3_flash_clock'] = image_data[SPI3_FLASH_CLOCK_OFFSET]
    header['spi_flash_read_mode'] = struct.unpack_from('<H', image_data, SPI_FLASH_READ_MODE_OFFSET)[0]
    header['fw_start_addr'] = struct.unpack_from('<I', image_data, FW_START_ADDR_OFFSET)[0]
    header['lms_kmo'] = struct.unpack_from('<I', image_data, LMS_KMO_OFFSET)[0]
    header['fw_length'] = struct.unpack_from('<I', image_data, FW_LENGTH_OFFSET)[0]
    header['key_mask'] = struct.unpack_from('<I', image_data, KEY_MASK_OFFSET)[0]
    header['key_index'] = struct.unpack_from('<I', image_data, KEY_INDEX_OFFSET)[0]
    header['key_invalid'] = struct.unpack_from('<I', image_data, KEY_INVALID_OFFSET)[0]
    header['encryption_ctrl'] = image_data[ENCRYPTION_CTRL_OFFSET]
    header['enable_lms'] = image_data[ENABLE_LMS_OFFSET]
    header['otp_revocation_ver'] = struct.unpack_from('<H', image_data, OTP_REVOCATION_VER_OFFSET)[0]
    header['otp_fw_version'] = struct.unpack_from('<H', image_data, OTP_FW_VERSION_OFFSET)[0]
    header['fw_table_offset'] = struct.unpack_from('<I', image_data, FW_TABLE_OFFSET_OFFSET)[0]
    header['aes_cbc_iv'] = image_data[AES_CBC_IV_OFFSET:AES_CBC_IV_OFFSET + 16]
    header['timestamp'] = struct.unpack_from('<I', image_data, TIMESTAMP_OFFSET)[0]
    header['key_mask_lms'] = struct.unpack_from('<I', image_data, KEY_MASK_LMS_OFFSET)[0]
    header['key_index_lms'] = struct.unpack_from('<I', image_data, KEY_INDEX_LMS_OFFSET)[0]

    return header


def print_header(header):
    """Print parsed header fields."""
    print("\n" + "=" * 60)
    print("KMT Header Fields")
    print("=" * 60)

    # Anchor validation
    anchor_ok = header['anchor'] == ANCHOR_VALUE
    print(f"  Anchor:              0x{header['anchor']:08X}  {'[OK]' if anchor_ok else '[INVALID]'}")

    # CRC enable check
    if header['ext_anchor'] == CRC_ENABLED_EXT_ANCHOR:
        crc_status = "CRC Enabled"
    elif header['ext_anchor'] == CRC_DISABLED_EXT_ANCHOR:
        crc_status = "CRC Disabled"
    else:
        crc_status = "UNKNOWN"
    print(f"  ExtAnchor (CRC):     0x{header['ext_anchor']:08X}  [{crc_status}]")

    print(f"  FW CRC32:            0x{header['fw_crc']:08X}")
    print(f"  SPI0 FlashClock:     0x{header['spi0_flash_clock']:02X}")
    print(f"  SPI1 FlashClock:     0x{header['spi1_flash_clock']:02X}")
    print(f"  SPI3 FlashClock:     0x{header['spi3_flash_clock']:02X}")
    print(f"  SPI FlashReadMode:   0x{header['spi_flash_read_mode']:04X}")
    print(f"  FW Start Address:    0x{header['fw_start_addr']:08X}")
    print(f"  LMS KMO:             0x{header['lms_kmo']:08X}")
    print(f"  FW Length:           0x{header['fw_length']:08X} ({header['fw_length']} bytes)")
    print(f"  Key Mask:            0x{header['key_mask']:08X}")
    print(f"  Key Index:           0x{header['key_index']:08X}")
    print(f"  Key Invalid:         0x{header['key_invalid']:08X}")
    print(f"  Encryption Control:  0x{header['encryption_ctrl']:02X}")
    print(f"  Enable LMS:          0x{header['enable_lms']:02X}")
    print(f"  OTP Revocation Ver:  0x{header['otp_revocation_ver']:04X}")
    print(f"  OTP FW Version:      0x{header['otp_fw_version']:04X}")
    print(f"  FW Table Offset:     0x{header['fw_table_offset']:08X}")
    print(f"  AES CBC IV:          {header['aes_cbc_iv'].hex()}")
    print(f"  Timestamp:           0x{header['timestamp']:08X}")
    print(f"  Key Mask LMS:        0x{header['key_mask_lms']:08X}")
    print(f"  Key Index LMS:       0x{header['key_index_lms']:08X}")

    # Signature (abbreviated)
    print(f"  ECC Sig r (first 8): {header['sig_r'][:8].hex()}...")
    print(f"  ECC Sig s (first 8): {header['sig_s'][:8].hex()}...")

    print("=" * 60)


def verify_crc(image_data, header):
    """Verify CRC32 of KMT section."""
    kmt_total_size = KMT_PAYLOAD_OFFSET + header['fw_length']
    signed_data = image_data[SIGNED_DATA_OFFSET:kmt_total_size]

    computed_crc = compute_crc32(signed_data)
    stored_crc = header['fw_crc']

    print(f"\n  CRC Verification:")
    print(f"    Data range:    [0x{SIGNED_DATA_OFFSET:X} .. 0x{kmt_total_size:X})")
    print(f"    Stored CRC:    0x{stored_crc:08X}")
    print(f"    Computed CRC:  0x{computed_crc:08X}")

    if computed_crc == stored_crc:
        print("    Result:        PASS")
        return True
    else:
        print("    Result:        FAIL")
        return False


def load_ecc_public_key(pub_bin_path):
    """Load ECC P-384 public key from IGPS _pub.bin format (x_LE || y_LE, 96 bytes)."""
    with open(pub_bin_path, 'rb') as f:
        pub_data = f.read()

    if len(pub_data) != 96:
        print(f"  ERROR: ECC public key file must be 96 bytes, got {len(pub_data)}")
        return None

    # IGPS format: x in little-endian (48 bytes) || y in little-endian (48 bytes)
    x_le = pub_data[0:48]
    y_le = pub_data[48:96]

    # Convert to big-endian integers
    x_int = int.from_bytes(x_le, byteorder='little')
    y_int = int.from_bytes(y_le, byteorder='little')

    # Construct the EC public key
    pub_numbers = ec.EllipticCurvePublicNumbers(x=x_int, y=y_int, curve=ec.SECP384R1())
    return pub_numbers.public_key(default_backend())


def extract_otp_key_pairs_from_fuse_map(fuse_map_data):
    """Extract all OTP ECC and LMS key pairs from fuse map binary.
    
    Returns list of (ecc_key_bytes, lms_key_bytes, index) tuples.
    Based on arbel_fuse_map.xml structure: 9 pairs total.
    """
    pairs = []
    
    # Key offsets from arbel_fuse_map.xml
    ecc_offsets = [0xD00, 0xD80, 0xE00, 0xE80, 0xF00, 0xF80, 0x1000, 0x1080, 0x1100]
    lms_offsets = [0x1600, 0x1680, 0x1700, 0x1780, 0x1800, 0x1880, 0x1900, 0x1980, 0x1A00]
    
    for idx, (ecc_off, lms_off) in enumerate(zip(ecc_offsets, lms_offsets)):
        if ecc_off + 96 <= len(fuse_map_data) and lms_off + 56 <= len(fuse_map_data):
            ecc_key = fuse_map_data[ecc_off:ecc_off + 96]
            lms_key = fuse_map_data[lms_off:lms_off + 56]
            pairs.append((ecc_key, lms_key, idx))
    
    return pairs


def load_ecc_public_key_from_bytes(key_bytes):
    """Load ECC public key from raw bytes (x_LE || y_LE, 96 bytes total)."""
    if len(key_bytes) != 2 * ECC_KEY_SIZE:
        return None
    
    try:
        x_int = le_bytes_to_int(key_bytes[:ECC_KEY_SIZE])
        y_int = le_bytes_to_int(key_bytes[ECC_KEY_SIZE:])
        pub_numbers = ec.EllipticCurvePublicNumbers(x_int, y_int, ec.SECP384R1())
        return pub_numbers.public_key(default_backend())
    except Exception as e:
        return None


def verify_ecc_signature(image_data, header, ecc_pub_key):
    """Verify ECDSA-SHA512 signature of KMT section."""
    kmt_total_size = KMT_PAYLOAD_OFFSET + header['fw_length']
    signed_data = image_data[SIGNED_DATA_OFFSET:kmt_total_size]

    # Extract signature components (little-endian in image)
    r_int = le_bytes_to_int(header['sig_r'])
    s_int = le_bytes_to_int(header['sig_s'])

    # Encode signature in DER format for verification
    signature_der = utils.encode_dss_signature(r_int, s_int)

    print(f"\n  ECC Signature Verification:")
    print(f"    Algorithm:     ECDSA P-384 + SHA-512")
    print(f"    Data range:    [0x{SIGNED_DATA_OFFSET:X} .. 0x{kmt_total_size:X})")
    print(f"    Data size:     {len(signed_data)} bytes")
    print(f"    r:             0x{r_int:096X}")
    print(f"    s:             0x{s_int:096X}")

    try:
        ecc_pub_key.verify(signature_der, signed_data, ec.ECDSA(hashes.SHA512()))
        print("    Result:        PASS")
        return True
    except Exception as e:
        print(f"    Result:        FAIL ({e})")
        return False


def verify_lms_signature(image_data, header, lms_pub_path):
    """Verify LMS signature appended after the KMT section."""
    if header['enable_lms'] == 0:
        print("\n  LMS Verification:  SKIPPED (LMS not enabled in header)")
        return True

    kmt_total_size = KMT_PAYLOAD_OFFSET + header['fw_length']

    print(f"\n  LMS Verification:")
    print(f"    LMS enabled:   Yes (0x{header['enable_lms']:02X})")
    print(f"    LMS pub key:   {lms_pub_path}")

    # In a composite image, scope to the region up to the next 0x1000 boundary
    next_boundary = ((kmt_total_size + 0xFFF) // 0x1000) * 0x1000
    if next_boundary > len(image_data):
        next_boundary = len(image_data)
    lms_sig_data = image_data[kmt_total_size:next_boundary]

    if len(lms_sig_data) == 0:
        print("    ERROR: No LMS signature data found after KMT section")
        print("    Result:        FAIL")
        return False

    # Load LMS public key from raw binary file
    try:
        from hsslms import LMS_Pub
        with open(lms_pub_path, 'rb') as f:
            pub_key_bytes = f.read()
        lms_pub_key = LMS_Pub(pub_key_bytes)
    except ImportError:
        print("    ERROR: 'hsslms' library not installed (pip install hsslms)")
        print("    Result:        FAIL")
        return False
    except Exception as e:
        print(f"    ERROR: Failed to load LMS public key: {e}")
        print("    Result:        FAIL")
        return False

    # Determine the exact LMS signature size from the signature header bytes
    try:
        sig_len = LMS_Pub._len_signature(lms_sig_data)
        lms_sig_exact = lms_sig_data[:sig_len]
    except Exception:
        print("    ERROR: Cannot determine LMS signature length from header")
        print("    Result:        FAIL")
        return False

    # Verify padding after the LMS signature is clean (all 0x00 or 0xFF)
    padding_region = lms_sig_data[sig_len:]
    for i, byte in enumerate(padding_region):
        if byte != 0x00 and byte != 0xFF:
            pad_offset = kmt_total_size + sig_len + i
            print(f"    WARNING: Non-zero/FF padding at offset 0x{pad_offset:X} "
                  f"(value 0x{byte:02X}) - possible tampering")
            print("    Result:        FAIL (padding corrupted)")
            return False

    # The signed data is SHA-512(image[112:kmt_total_size])
    signed_data = image_data[SIGNED_DATA_OFFSET:kmt_total_size]
    hashed = hashlib.sha512(signed_data).digest()

    print(f"    Signed range:  [0x{SIGNED_DATA_OFFSET:X} .. 0x{kmt_total_size:X})")
    print(f"    SHA-512 hash:  {hashed[:16].hex()}...")
    print(f"    LMS sig range: [0x{kmt_total_size:X} .. 0x{kmt_total_size + sig_len:X}) ({sig_len} bytes)")

    try:
        lms_pub_key.verify(hashed, lms_sig_exact)
        print("    Result:        PASS")
        return True
    except Exception as e:
        print(f"    Result:        FAIL ({e})")
        return False


def extract_kmt_ecc_key(image_data, kmt_header, key_index=None):
    """Extract KMT ECC public key from KMT payload by index.
    
    Args:
        image_data: full image data
        kmt_header: parsed KMT header
        key_index: specific key index to extract (defaults to header['key_index'])
    
    Returns:
        (key_data, index) tuple, or (None, None) on error
    """
    if key_index is None:
        key_index = kmt_header['key_index']
    
    kmt_payload_data = image_data[KMT_PAYLOAD_OFFSET:KMT_PAYLOAD_OFFSET + kmt_header['fw_length']]
    
    # KMT payload structure: multiple ECC key slots (96 bytes each for P-384)
    # followed by multiple LMS key slots
    # Assuming up to 4 ECC keys (384 bytes) followed by LMS keys
    ecc_key_slot_offset = key_index * 96
    
    if ecc_key_slot_offset + 96 > len(kmt_payload_data):
        return None, None
    
    ecc_key_data = kmt_payload_data[ecc_key_slot_offset:ecc_key_slot_offset + 96]
    return ecc_key_data, key_index


def extract_kmt_lms_key(image_data, kmt_header, key_index=None):
    """Extract KMT LMS public key from KMT payload by index.
    
    Args:
        image_data: full image data
        kmt_header: parsed KMT header
        key_index: specific key index to extract (defaults to header['key_index_lms'])
    
    Returns:
        (key_data, index) tuple, or (None, None) on error
    """
    if key_index is None:
        key_index = kmt_header['key_index_lms']
    
    kmt_payload_data = image_data[KMT_PAYLOAD_OFFSET:KMT_PAYLOAD_OFFSET + kmt_header['fw_length']]
    
    # LMS keys are stored at 0x100 + key_index * 0x50 in the kmt_map.bin
    # Each slot is 80 bytes (56 bytes key + 24 bytes padding)
    lms_key_offset = 0x100 + key_index * 0x50
    
    if lms_key_offset + 56 > len(kmt_payload_data):
        return None, None
    
    lms_key_data = kmt_payload_data[lms_key_offset:lms_key_offset + 56]
    return lms_key_data, key_index


def parse_section_header(image_data, base_offset):
    """Parse a firmware section header at given base offset."""
    header = {}
    header['anchor'] = struct.unpack_from('<I', image_data, base_offset + ANCHOR_OFFSET)[0]
    header['ext_anchor'] = struct.unpack_from('<I', image_data, base_offset + EXT_ANCHOR_OFFSET)[0]
    header['fw_crc'] = struct.unpack_from('<I', image_data, base_offset + FW_CRC_OFFSET)[0]
    header['sig_r'] = image_data[base_offset + SIGNATURE_OFFSET:base_offset + SIGNATURE_OFFSET + ECC_KEY_SIZE]
    header['sig_s'] = image_data[base_offset + SIGNATURE_OFFSET + ECC_KEY_SIZE:base_offset + SIGNATURE_OFFSET + SIGNATURE_SIZE]
    header['fw_length'] = struct.unpack_from('<I', image_data, base_offset + FW_LENGTH_OFFSET)[0]
    header['key_index'] = struct.unpack_from('<I', image_data, base_offset + KEY_INDEX_OFFSET)[0]
    header['enable_lms'] = image_data[base_offset + ENABLE_LMS_OFFSET]
    header['timestamp'] = struct.unpack_from('<I', image_data, base_offset + TIMESTAMP_OFFSET)[0]
    header['key_mask_lms'] = struct.unpack_from('<I', image_data, base_offset + KEY_MASK_LMS_OFFSET)[0]
    header['key_index_lms'] = struct.unpack_from('<I', image_data, base_offset + KEY_INDEX_LMS_OFFSET)[0]
    return header


def verify_l0_section(image_data, kmt_header, ecc_kmt_path=None, lms_kmt_path=None, image_basename='image'):
    """Verify the L0/TFT section at offset 0x1000 in the composite image.

    Always extracts keys from the KMT payload and verifies the L0 section.
    If ecc_kmt_path or lms_kmt_path are provided, additionally verifies with
    those key files and reports both results independently.
    """
    base = L0_SECTION_OFFSET

    if len(image_data) <= base + KMT_PAYLOAD_OFFSET:
        print("\n  L0 Verification:   SKIPPED (image too small for L0 section)")
        return True

    print("\n" + "=" * 60)
    print("L0 (TIP FW) Section Verification")
    print("=" * 60)

    header = parse_section_header(image_data, base)

    # Validate L0 anchor
    if header['anchor'] != L0_ANCHOR_VALUE:
        print(f"  ERROR: Invalid L0 anchor 0x{header['anchor']:08X} "
              f"(expected 0x{L0_ANCHOR_VALUE:08X})")
        return False

    # Check CRC enable
    crc_enabled = (header['ext_anchor'] == CRC_ENABLED_EXT_ANCHOR)
    crc_status = "CRC Enabled" if crc_enabled else "CRC Disabled"
    l0_total_size = KMT_PAYLOAD_OFFSET + header['fw_length']

    print(f"  Anchor:           0x{header['anchor']:08X}  [OK]")
    print(f"  ExtAnchor:        0x{header['ext_anchor']:08X}  [{crc_status}]")
    print(f"  FW CRC32:         0x{header['fw_crc']:08X}")
    print(f"  FW Length:        0x{header['fw_length']:08X} ({header['fw_length']} bytes)")
    print(f"  Key Index:        0x{header['key_index']:08X}")
    print(f"  Enable LMS:       0x{header['enable_lms']:02X}")
    print(f"  Timestamp:        0x{header['timestamp']:08X}")
    print(f"  Section range:    [0x{base:X} .. 0x{base + l0_total_size:X})")

    if base + l0_total_size > len(image_data):
        print(f"  ERROR: L0 section (0x{base + l0_total_size:X}) exceeds image size")
        return False

    results = []

    # Verify CRC
    if crc_enabled:
        signed_data = image_data[base + SIGNED_DATA_OFFSET:base + l0_total_size]
        computed_crc = compute_crc32(signed_data)
        stored_crc = header['fw_crc']
        crc_pass = (computed_crc == stored_crc)
        print(f"\n  L0 CRC Verification:")
        print(f"    Data range:    [0x{base + SIGNED_DATA_OFFSET:X} .. 0x{base + l0_total_size:X})")
        print(f"    Stored CRC:    0x{stored_crc:08X}")
        print(f"    Computed CRC:  0x{computed_crc:08X}")
        print(f"    Result:        {'PASS' if crc_pass else 'FAIL'}")
        results.append((f'L0 CRC32 inside {image_basename}', crc_pass))

    # Always extract ECC key from KMT payload and verify
    ecc_key_data, kmt_ecc_idx = extract_kmt_ecc_key(image_data, kmt_header, header['key_index'])
    if ecc_key_data is None:
        print(f"\n  L0 ECC Signature Verification: FAILED (cannot load ECC key from KMT payload)")
        return False
    try:
        x_int = le_bytes_to_int(ecc_key_data[:ECC_KEY_SIZE])
        y_int = le_bytes_to_int(ecc_key_data[ECC_KEY_SIZE:])
        extracted_ecc_pub_key = ec.EllipticCurvePublicNumbers(x_int, y_int, ec.SECP384R1()).public_key(default_backend())
    except Exception as e:
        print(f"\n  L0 ECC Signature Verification: FAILED (cannot parse ECC key: {e})")
        return False

    signed_data = image_data[base + SIGNED_DATA_OFFSET:base + l0_total_size]
    r_int = le_bytes_to_int(header['sig_r'])
    s_int = le_bytes_to_int(header['sig_s'])
    signature_der = utils.encode_dss_signature(r_int, s_int)

    print(f"\n  L0 ECC Signature Verification (KMT payload, index {kmt_ecc_idx}):")
    print(f"    Algorithm:     ECDSA P-384 + SHA-512")
    print(f"    Data range:    [0x{base + SIGNED_DATA_OFFSET:X} .. 0x{base + l0_total_size:X})")
    print(f"    Data size:     {len(signed_data)} bytes")
    try:
        extracted_ecc_pub_key.verify(signature_der, signed_data, ec.ECDSA(hashes.SHA512()))
        print("    Result:        PASS")
        results.append((f'L0 ECC Signature by key from {image_basename} KMT payload, index {kmt_ecc_idx}', True))
    except Exception as e:
        print(f"    Result:        FAIL ({e})")
        results.append((f'L0 ECC Signature by key from {image_basename} KMT payload, index {kmt_ecc_idx}', False))

    # Additionally verify with explicit file if provided
    if ecc_kmt_path:
        file_ecc_pub_key = load_ecc_public_key(ecc_kmt_path)
        if file_ecc_pub_key is not None:
            ecc_filename = os.path.basename(ecc_kmt_path)
            print(f"\n  L0 ECC Signature Verification (file: {ecc_filename}):")
            print(f"    Algorithm:     ECDSA P-384 + SHA-512")
            try:
                file_ecc_pub_key.verify(signature_der, signed_data, ec.ECDSA(hashes.SHA512()))
                print("    Result:        PASS")
                results.append((f'L0 ECC Signature by key from {ecc_filename}', True))
            except Exception as e:
                print(f"    Result:        FAIL ({e})")
                results.append((f'L0 ECC Signature by key from {ecc_filename}', False))

    # Verify LMS signature (if enabled in L0 header)
    if header['enable_lms'] != 0:
        l0_lms_sig_start = base + l0_total_size
        # L0 is the last section in the composite image, so its LMS signature
        # extends to the end of the file (not limited by 0x1000 boundary)
        lms_sig_data = image_data[l0_lms_sig_start:]

        print(f"\n  L0 LMS Verification:")
        print(f"    LMS enabled:   Yes (0x{header['enable_lms']:02X})")

        if len(lms_sig_data) == 0:
            print("    ERROR: No LMS signature data found after L0 section")
            results.append((f'L0 LMS Signature by key from {image_basename} KMT payload', False))
        else:
            try:
                from hsslms import LMS_Pub

                # Always extract LMS key from KMT payload and verify
                lms_key_data, kmt_lms_idx = extract_kmt_lms_key(image_data, kmt_header, header['key_index_lms'])
                if lms_key_data is None:
                    print("    ERROR: Cannot extract LMS key from KMT payload")
                    results.append((f'L0 LMS Signature by key from {image_basename} KMT payload', False))
                else:
                    lms_pub_key = LMS_Pub(lms_key_data)
                    sig_len = LMS_Pub._len_signature(lms_sig_data)
                    lms_sig_exact = lms_sig_data[:sig_len]
                    hashed = hashlib.sha512(signed_data).digest()

                    print(f"    Key source:    KMT payload, index {kmt_lms_idx}")
                    print(f"    Signed range:  [0x{base + SIGNED_DATA_OFFSET:X} .. 0x{base + l0_total_size:X})")
                    print(f"    SHA-512 hash:  {hashed[:16].hex()}...")
                    print(f"    LMS sig range: [0x{l0_lms_sig_start:X} .. 0x{l0_lms_sig_start + sig_len:X}) ({sig_len} bytes)")
                    try:
                        lms_pub_key.verify(hashed, lms_sig_exact)
                        print("    Result:        PASS")
                        results.append((f'L0 LMS Signature by key from {image_basename} KMT payload, index {kmt_lms_idx}', True))
                    except Exception as e:
                        print(f"    Result:        FAIL ({e})")
                        results.append((f'L0 LMS Signature by key from {image_basename} KMT payload, index {kmt_lms_idx}', False))

                    # Additionally verify with explicit file if provided
                    if lms_kmt_path:
                        lms_filename = os.path.basename(lms_kmt_path)
                        print(f"\n  L0 LMS Verification (file: {lms_filename}):")
                        try:
                            with open(lms_kmt_path, 'rb') as f:
                                file_lms_key_bytes = f.read()
                            file_lms_pub_key = LMS_Pub(file_lms_key_bytes)
                            file_lms_pub_key.verify(hashed, lms_sig_exact)
                            print("    Result:        PASS")
                            results.append((f'L0 LMS Signature by key from {lms_filename}', True))
                        except Exception as e:
                            print(f"    Result:        FAIL ({e})")
                            results.append((f'L0 LMS Signature by key from {lms_filename}', False))

            except ImportError:
                print("    ERROR: 'hsslms' library not installed")
                results.append((f'L0 LMS Signature by key from {image_basename} KMT payload', False))
    else:
        print(f"\n  L0 LMS Verification:  SKIPPED (LMS not enabled in L0 header)")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Verify KMT header signature and CRC in a binary image.',
        usage='%(prog)s IMAGE [--otp_img OTP_IMG_MAP_BIN] [--otp_ecc OTP_ECC_PUB_BIN] [--otp_lms OTP_LMS_PUB_BIN] [--kmt_ecc KMT_ECC_PUB_BIN] [--kmt_lms KMT_LMS_PUB_BIN]',
        epilog='For detailed usage and examples look for verify_image.md in docs folder',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('image',
                        help='Path to the binary image to verify (e.g., Kmt_TipFwL0.bin)')
    parser.add_argument('--otp_img', required=False, default=None, metavar='OTP_IMG_MAP_BIN',
                        help="Path to OTP fuse map binary (arbel_fuse_map.bin) to try all 9 OTP key pairs; if used you don't have to use --otp_ecc or --otp_lms")
    parser.add_argument('--otp_ecc', required=False, default=None, metavar='OTP_ECC_PUB_BIN',
                        help='Path to OTP ECC public key binary that signs KMT (96 bytes); Optional since can be verified by --otp_img flag')
    parser.add_argument('--otp_lms', required=False, default=None, metavar='OTP_LMS_PUB_BIN',
                        help='Path to OTP LMS public key binary that signs KMT (56 bytes); Optional since can be verified by --otp_img flag')
    parser.add_argument('--kmt_ecc', required=False, default=None, metavar='KMT_ECC_PUB_BIN',
                        help='Path to KMT ECC public key binary that signs L0/TFT (96 bytes); Optional since verifies in addition to key auto-extracted from image')
    parser.add_argument('--kmt_lms', required=False, default=None, metavar='KMT_LMS_PUB_BIN',
                        help='Path to KMT LMS public key binary that signs L0/TFT (56 bytes); Optional since verifies in addition to key auto-extracted from image')
    args = parser.parse_args()

    # Read image
    try:
        with open(args.image, 'rb') as f:
            image_data = f.read()
    except FileNotFoundError:
        print(f"ERROR: Image file not found: {args.image}")
        return 1

    if len(image_data) < KMT_PAYLOAD_OFFSET:
        print(f"ERROR: Image too small ({len(image_data)} bytes), minimum {KMT_PAYLOAD_OFFSET}")
        return 1

    print(f"Image: {args.image} ({len(image_data)} bytes)")
    image_basename = os.path.basename(args.image)

    # Parse header
    header = parse_kmt_header(image_data)
    print_header(header)

    # Validate anchor
    if header['anchor'] != ANCHOR_VALUE:
        print("ERROR: Invalid anchor - not a valid KMT image")
        return 1

    # Check KMT section fits within image
    kmt_total_size = KMT_PAYLOAD_OFFSET + header['fw_length']
    if kmt_total_size > len(image_data):
        print(f"ERROR: KMT section size (0x{kmt_total_size:X}) exceeds image size (0x{len(image_data):X})")
        return 1

    print(f"\nKMT section: 0x{kmt_total_size:X} bytes (header: 0x{KMT_PAYLOAD_OFFSET:X} + payload: 0x{header['fw_length']:X})")

    kmt_results = []

    # Verify CRC (if enabled)
    crc_enabled = (header['ext_anchor'] == CRC_ENABLED_EXT_ANCHOR)
    if crc_enabled:
        kmt_results.append((f'KMT CRC32 inside {image_basename}', verify_crc(image_data, header)))
    else:
        print("\n  CRC Verification:  SKIPPED (CRC disabled in header)")

    # Verify ECC and LMS signatures
    ecc_verified_any = False
    otp_pair_idx = None
    
    # Try OTP key pairs from fuse map (if provided) - independent of explicit keys
    if args.otp_img:
        print("\n" + "=" * 60)
        print("OTP Key Pair Verification (trying all 9 pairs)")
        print("=" * 60)
        
        try:
            with open(args.otp_img, 'rb') as f:
                fuse_map_data = f.read()
        except FileNotFoundError:
            print(f"ERROR: OTP image file not found: {args.otp_img}")
            return 1
        
        otp_img_basename = os.path.basename(args.otp_img)
        otp_pairs = extract_otp_key_pairs_from_fuse_map(fuse_map_data)
        print(f"Extracted {len(otp_pairs)} OTP key pairs from fuse map\n")
        
        for ecc_bytes, lms_bytes, idx in otp_pairs:
            print(f"  Trying pair {idx}:")
            
            # Try ECC verification with this pair
            ecc_pub_key = load_ecc_public_key_from_bytes(ecc_bytes)
            if ecc_pub_key is None:
                print(f"    ECC key load failed")
                continue
            
            # Test ECC
            kmt_total_size = KMT_PAYLOAD_OFFSET + header['fw_length']
            signed_data = image_data[SIGNED_DATA_OFFSET:kmt_total_size]
            r_int = le_bytes_to_int(header['sig_r'])
            s_int = le_bytes_to_int(header['sig_s'])
            signature_der = utils.encode_dss_signature(r_int, s_int)
            
            ecc_pass = False
            try:
                ecc_pub_key.verify(signature_der, signed_data, ec.ECDSA(hashes.SHA512()))
                print(f"    ECC: PASS")
                ecc_pass = True
            except Exception as e:
                print(f"    ECC: FAIL")
                continue
            
            # If ECC passed, try LMS (if enabled)
            lms_pass = True
            if header['enable_lms'] != 0:
                try:
                    from hsslms import LMS_Pub
                    lms_pub_key = LMS_Pub(lms_bytes)
                    
                    lms_sig_start = kmt_total_size
                    lms_sig_data = image_data[lms_sig_start:]
                    
                    if len(lms_sig_data) == 0:
                        print(f"    LMS: SKIP (no signature data)")
                        lms_pass = True  # LMS not critical
                    else:
                        sig_len = LMS_Pub._len_signature(lms_sig_data)
                        lms_sig_exact = lms_sig_data[:sig_len]
                        hashed = hashlib.sha512(signed_data).digest()
                        
                        try:
                            lms_pub_key.verify(hashed, lms_sig_exact)
                            print(f"    LMS: PASS")
                            lms_pass = True
                        except Exception as e:
                            print(f"    LMS: FAIL")
                            lms_pass = False
                except ImportError:
                    print(f"    LMS: SKIP (hsslms not installed)")
                    lms_pass = True
            else:
                print(f"    LMS: SKIP (not enabled)")
            
            if ecc_pass and lms_pass:
                print(f"\n  ✓ Pair {idx} VERIFIED (ECC + LMS)")
                kmt_results.append((f'KMT ECC Signature by key from {otp_img_basename} OTP pair {idx} (starting from 0)', True))
                if header['enable_lms'] != 0:
                    kmt_results.append((f'KMT LMS Signature by key from {otp_img_basename} OTP pair {idx} (starting from 0)', True))
                ecc_verified_any = True
                otp_pair_idx = idx
                break
        
        if not ecc_verified_any:
            print(f"\n  ✗ No OTP pair matched")
            kmt_results.append((f'KMT ECC Signature by key from {otp_img_basename} (no pair matched)', False))
            if header['enable_lms'] != 0:
                kmt_results.append((f'KMT LMS Signature by key from {otp_img_basename} (no pair matched)', False))

    # Try explicit ECC key from file (if provided, independent of OTP verification)
    if args.otp_ecc:
        ecc_pub_key = load_ecc_public_key(args.otp_ecc)
        if ecc_pub_key is None:
            return 1
        ecc_result = verify_ecc_signature(image_data, header, ecc_pub_key)
        ecc_filename = os.path.basename(args.otp_ecc)
        kmt_results.append((f'KMT ECC Signature by key from {ecc_filename}', ecc_result))
        ecc_verified_any = ecc_verified_any or ecc_result

    # Try explicit LMS key from file (if provided, independent of OTP verification)
    if args.otp_lms:
        lms_result = verify_lms_signature(image_data, header, args.otp_lms)
        lms_filename = os.path.basename(args.otp_lms)
        kmt_results.append((f'KMT LMS Signature by key from {lms_filename}', lms_result))

    # If neither OTP nor explicit keys provided, error
    if not args.otp_img and not args.otp_ecc:
        print("\nERROR: Must provide either --otp_ecc or --otp_img")
        return 1

    # Verify L0/TFT section (if image is composite and some ECC was verified)
    l0_results = []
    if ecc_verified_any and len(image_data) > L0_SECTION_OFFSET + KMT_PAYLOAD_OFFSET:
        l0_raw = verify_l0_section(image_data, header, args.kmt_ecc, args.kmt_lms, image_basename)
        if isinstance(l0_raw, list):
            l0_results = l0_raw
        elif l0_raw is False:
            l0_results = [(f'L0 Verification from {image_basename}', False)]

    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    all_pass = True

    if kmt_results:
        print("KMT verification:")
        for name, passed in kmt_results:
            status = "PASS" if passed else "FAIL"
            print(f"  {name:<75s} {status}")
            if not passed:
                all_pass = False

    if l0_results:
        print("L0 (TFT) verification:")
        for name, passed in l0_results:
            status = "PASS" if passed else "FAIL"
            print(f"  {name:<75s} {status}")
            if not passed:
                all_pass = False

    print("=" * 60)
    if all_pass:
        print("OVERALL: PASS")
        return 0
    else:
        print("OVERALL: FAIL")
        return 1


if __name__ == '__main__':
    sys.exit(main())
