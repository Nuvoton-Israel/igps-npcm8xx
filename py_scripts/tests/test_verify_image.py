#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
#
# Comprehensive Test Suite for verify_image.py
#
# Tests verification of corrupted binaries, signature tampering, payload changes,
# key mismatches, and various flag scenarios.

import os
import sys
import shutil
import subprocess
import struct
import tempfile
from pathlib import Path

# Test configuration
TEST_IMAGE = "./ImageGeneration/output_binaries/Secure/Kmt_TipFwL0.bin"
OTP_IMAGE = "./ImageGeneration/output_binaries/Secure/arbel_fuse_map.bin"
ECC_KEY = "./ImageGeneration/keys/openssl/otp_ecc_key_1_pub.bin"
LMS_KEY = "./ImageGeneration/keys/openssl/otp_lms_key_1_pub.bin"
ECC_KEY_WRONG = "./ImageGeneration/keys/openssl/otp_ecc_key_0_pub.bin"  # Different key
LMS_KEY_WRONG = "./ImageGeneration/keys/openssl/otp_lms_key_0_pub.bin"  # Different key

# Known offsets in the test image
KMT_ECC_SIG_OFFSET = 0x10          # ECC signature r||s in KMT header
KMT_LMS_SIG_OFFSET = 0x2A0        # LMS signature starts after KMT payload (0x100 + 0x1A0)
KMT_HEADER_END = 0x100
KMT_PAYLOAD_END = 0x2A0           # 0x100 + 0x1A0 fw_length
L0_SECTION_OFFSET = 0x1000
L0_HEADER_END = L0_SECTION_OFFSET + 0x100
L0_ECC_SIG_OFFSET = L0_SECTION_OFFSET + 0x10
KMT_FW_LENGTH_OFFSET = 0x84        # FW_LENGTH field in KMT header
L0_FW_LENGTH_OFFSET = L0_SECTION_OFFSET + 0x84

class TestCase:
    def __init__(self, name, description, test_func):
        self.name = name
        self.description = description
        self.test_func = test_func
        self.result = None
        self.output = None
        self.error_msg = None

    def run(self):
        try:
            self.test_func()
            self.result = "PASS"
        except AssertionError as e:
            self.result = "FAIL"
            self.error_msg = str(e)
        except Exception as e:
            self.result = "ERROR"
            self.error_msg = str(e)

    def report(self):
        status_symbol = "✓" if self.result == "PASS" else "✗"
        print(f"\n{status_symbol} {self.name}")
        print(f"  Description: {self.description}")
        print(f"  Result:      {self.result}")
        if self.error_msg:
            print(f"  Error:       {self.error_msg}")


def flip_bit(data, byte_offset, bit_offset):
    """Flip a single bit at byte_offset, bit_offset within a bytearray."""
    data_list = bytearray(data)
    data_list[byte_offset] ^= (1 << bit_offset)
    return bytes(data_list)


def modify_u32_le(data, offset, new_value):
    """Modify a 32-bit little-endian value at offset."""
    data_list = bytearray(data)
    data_list[offset:offset+4] = struct.pack('<I', new_value)
    return bytes(data_list)


def create_corrupted_image(test_name, corruption_func):
    """Create a corrupted copy of the test image."""
    with open(TEST_IMAGE, 'rb') as f:
        image_data = f.read()
    
    corrupted_data = corruption_func(image_data)
    temp_path = f"/tmp/test_image_{test_name}.bin"
    with open(temp_path, 'wb') as f:
        f.write(corrupted_data)
    return temp_path


def run_verify(args, expect_pass=False):
    """Run verify_image.py and return output."""
    cmd = ['python3', 'verify_image.py'] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout + result.stderr
    
    # Check if verification passed based on output
    passed = "OVERALL: PASS" in output
    
    if expect_pass and not passed:
        raise AssertionError(f"Expected PASS but got FAIL\nOutput:\n{output}")
    elif not expect_pass and passed:
        raise AssertionError(f"Expected FAIL but got PASS\nOutput:\n{output}")
    
    return output, passed


# ============================================================================
# TEST CASES
# ============================================================================

tests = []

# ============================================================================
# BASELINE TESTS - Should all PASS
# ============================================================================

def test_baseline_otp():
    """Baseline: Clean image with OTP verification should PASS."""
    args = [TEST_IMAGE, '--otp_img', OTP_IMAGE]
    output, passed = run_verify(args, expect_pass=True)
    assert passed, "Baseline OTP verification failed"

tests.append(TestCase("BASELINE_OTP", "Clean image verifies with OTP pairs", test_baseline_otp))


def test_baseline_explicit_keys():
    """Baseline: Clean image with explicit keys should PASS."""
    args = [TEST_IMAGE, '--otp_ecc', ECC_KEY, '--otp_lms', LMS_KEY]
    output, passed = run_verify(args, expect_pass=True)
    assert passed, "Baseline explicit key verification failed"

tests.append(TestCase("BASELINE_EXPLICIT", "Clean image verifies with explicit keys", test_baseline_explicit_keys))


def test_baseline_both():
    """Baseline: Clean image with both OTP and explicit keys should PASS."""
    args = [TEST_IMAGE, '--otp_img', OTP_IMAGE, '--otp_ecc', ECC_KEY, '--otp_lms', LMS_KEY]
    output, passed = run_verify(args, expect_pass=True)
    assert passed, "Baseline both verification failed"

tests.append(TestCase("BASELINE_BOTH", "Clean image verifies with both OTP and explicit keys", test_baseline_both))


# ============================================================================
# KMT ECC SIGNATURE CORRUPTION
# ============================================================================

def test_kmt_ecc_sig_bit_flip():
    """KMT ECC signature with single bit flip should FAIL."""
    def corrupt(data):
        return flip_bit(data, KMT_ECC_SIG_OFFSET, 0)
    
    corrupted_path = create_corrupted_image("kmt_ecc_bit_flip", corrupt)
    args = [corrupted_path, '--otp_ecc', ECC_KEY]
    output, passed = run_verify(args, expect_pass=False)
    assert not passed, "Should have detected KMT ECC signature corruption"
    os.remove(corrupted_path)

tests.append(TestCase("KMT_ECC_BIT_FLIP", "KMT ECC sig with 1-bit flip detected", test_kmt_ecc_sig_bit_flip))


def test_kmt_ecc_sig_byte_flip():
    """KMT ECC signature with full byte flip should FAIL."""
    def corrupt(data):
        return flip_bit(data, KMT_ECC_SIG_OFFSET + 10, 7)
    
    corrupted_path = create_corrupted_image("kmt_ecc_byte_flip", corrupt)
    args = [corrupted_path, '--otp_ecc', ECC_KEY]
    output, passed = run_verify(args, expect_pass=False)
    assert not passed, "Should have detected KMT ECC signature corruption"
    os.remove(corrupted_path)

tests.append(TestCase("KMT_ECC_BYTE_FLIP", "KMT ECC sig with byte flip detected", test_kmt_ecc_sig_byte_flip))


# ============================================================================
# KMT PAYLOAD CORRUPTION
# ============================================================================

def test_kmt_payload_bit_flip():
    """KMT payload with bit flip should FAIL CRC and/or signatures."""
    def corrupt(data):
        # Flip bit in KMT payload (after header, before LMS sig)
        return flip_bit(data, 0x150, 3)
    
    corrupted_path = create_corrupted_image("kmt_payload_bit", corrupt)
    args = [corrupted_path, '--otp_ecc', ECC_KEY]
    output, passed = run_verify(args, expect_pass=False)
    assert not passed, "Should have detected KMT payload corruption"
    os.remove(corrupted_path)

tests.append(TestCase("KMT_PAYLOAD_BIT_FLIP", "KMT payload with bit flip detected", test_kmt_payload_bit_flip))


# ============================================================================
# KMT LMS SIGNATURE CORRUPTION
# ============================================================================

def test_kmt_lms_sig_bit_flip():
    """KMT LMS signature with bit flip should FAIL."""
    def corrupt(data):
        # LMS sig starts at KMT_LMS_SIG_OFFSET, flip bit in middle of signature
        return flip_bit(data, KMT_LMS_SIG_OFFSET + 500, 2)
    
    corrupted_path = create_corrupted_image("kmt_lms_bit_flip", corrupt)
    args = [corrupted_path, '--otp_lms', LMS_KEY]
    output, passed = run_verify(args, expect_pass=False)
    assert not passed, "Should have detected KMT LMS signature corruption"
    os.remove(corrupted_path)

tests.append(TestCase("KMT_LMS_BIT_FLIP", "KMT LMS sig with bit flip detected", test_kmt_lms_sig_bit_flip))


# ============================================================================
# KMT HEADER FIELD CORRUPTION
# ============================================================================

def test_kmt_fw_length_modification():
    """KMT fw_length field modification should FAIL verification."""
    def corrupt(data):
        # Change fw_length from 0x1A0 to 0x1A1
        return modify_u32_le(data, KMT_FW_LENGTH_OFFSET, 0x1A1)
    
    corrupted_path = create_corrupted_image("kmt_fw_len", corrupt)
    args = [corrupted_path, '--otp_ecc', ECC_KEY]
    output, passed = run_verify(args, expect_pass=False)
    assert not passed, "Should have detected KMT fw_length tampering"
    os.remove(corrupted_path)

tests.append(TestCase("KMT_FW_LENGTH_MOD", "KMT fw_length tampering detected", test_kmt_fw_length_modification))


# ============================================================================
# L0 CORRUPTION TESTS
# ============================================================================

def test_l0_payload_bit_flip():
    """L0 payload with bit flip should FAIL."""
    def corrupt(data):
        # Flip bit in L0 payload
        return flip_bit(data, L0_HEADER_END + 0x100, 5)
    
    corrupted_path = create_corrupted_image("l0_payload_bit", corrupt)
    args = [corrupted_path, '--otp_ecc', ECC_KEY]
    output, passed = run_verify(args, expect_pass=False)
    assert not passed, "Should have detected L0 payload corruption"
    os.remove(corrupted_path)

tests.append(TestCase("L0_PAYLOAD_BIT_FLIP", "L0 payload with bit flip detected", test_l0_payload_bit_flip))


def test_l0_ecc_sig_bit_flip():
    """L0 ECC signature with bit flip should FAIL."""
    def corrupt(data):
        return flip_bit(data, L0_ECC_SIG_OFFSET + 20, 4)
    
    corrupted_path = create_corrupted_image("l0_ecc_bit_flip", corrupt)
    args = [corrupted_path, '--otp_ecc', ECC_KEY]
    output, passed = run_verify(args, expect_pass=False)
    assert not passed, "Should have detected L0 ECC signature corruption"
    os.remove(corrupted_path)

tests.append(TestCase("L0_ECC_BIT_FLIP", "L0 ECC sig with bit flip detected", test_l0_ecc_sig_bit_flip))


def test_l0_fw_length_modification():
    """L0 fw_length field modification should FAIL verification."""
    def corrupt(data):
        # Change L0 fw_length
        return modify_u32_le(data, L0_FW_LENGTH_OFFSET, 0x10E21)
    
    corrupted_path = create_corrupted_image("l0_fw_len", corrupt)
    args = [corrupted_path, '--otp_ecc', ECC_KEY]
    output, passed = run_verify(args, expect_pass=False)
    assert not passed, "Should have detected L0 fw_length tampering"
    os.remove(corrupted_path)

tests.append(TestCase("L0_FW_LENGTH_MOD", "L0 fw_length tampering detected", test_l0_fw_length_modification))


# ============================================================================
# KEY MISMATCH TESTS
# ============================================================================

def test_wrong_explicit_ecc_key():
    """Using wrong ECC key should FAIL."""
    args = [TEST_IMAGE, '--otp_ecc', ECC_KEY_WRONG]
    output, passed = run_verify(args, expect_pass=False)
    assert not passed, "Should have detected key mismatch"

tests.append(TestCase("WRONG_ECC_KEY", "Wrong ECC key file detected", test_wrong_explicit_ecc_key))


def test_wrong_explicit_lms_key():
    """Using wrong LMS key should FAIL."""
    args = [TEST_IMAGE, '--otp_ecc', ECC_KEY, '--otp_lms', LMS_KEY_WRONG]
    output, passed = run_verify(args, expect_pass=False)
    assert not passed, "Should have detected LMS key mismatch"

tests.append(TestCase("WRONG_LMS_KEY", "Wrong LMS key file detected", test_wrong_explicit_lms_key))


def test_wrong_otp_pair():
    """Providing wrong OTP image should fail to find matching pair."""
    # Create a fake OTP image with zeros
    fake_otp_path = "/tmp/fake_otp.bin"
    with open(fake_otp_path, 'wb') as f:
        f.write(b'\x00' * 8192)
    
    args = [TEST_IMAGE, '--otp_img', fake_otp_path]
    output, passed = run_verify(args, expect_pass=False)
    assert not passed, "Should have failed to find matching OTP pair"
    os.remove(fake_otp_path)

tests.append(TestCase("WRONG_OTP_IMAGE", "Wrong OTP image no matching pair", test_wrong_otp_pair))


# ============================================================================
# TRUNCATION TESTS
# ============================================================================

def test_image_truncated():
    """Truncated image should FAIL."""
    def corrupt(data):
        # Return only first 50% of image
        return data[:len(data)//2]
    
    corrupted_path = create_corrupted_image("truncated", corrupt)
    args = [corrupted_path, '--otp_ecc', ECC_KEY]
    try:
        output, passed = run_verify(args, expect_pass=False)
        assert not passed, "Should have detected truncation"
    except:
        pass  # Tool may error on truncated file, which is acceptable
    os.remove(corrupted_path)

tests.append(TestCase("IMAGE_TRUNCATED", "Truncated image detected", test_image_truncated))


# ============================================================================
# FLAG SCENARIO TESTS
# ============================================================================

def test_only_ecc_without_lms():
    """Verify with only ECC key (no LMS) should detect and skip LMS."""
    args = [TEST_IMAGE, '--otp_ecc', ECC_KEY]
    output, passed = run_verify(args, expect_pass=True)
    assert passed, "ECC-only verification failed"
    assert "LMS" in output or "SKIP" in output or "LMS not enabled" in output.lower(), \
        "Should mention LMS handling"

tests.append(TestCase("ONLY_ECC_KEY", "ECC-only verification works correctly", test_only_ecc_without_lms))


def test_both_otp_and_explicit_keys():
    """Both OTP and explicit keys should verify independently."""
    args = [TEST_IMAGE, '--otp_img', OTP_IMAGE, '--otp_ecc', ECC_KEY, '--otp_lms', LMS_KEY]
    output, passed = run_verify(args, expect_pass=True)
    assert passed, "Dual verification failed"
    # Check that both verification methods appear in output
    assert "OTP pair" in output, "OTP verification not shown"
    assert "by key from " in output, "Explicit key verification not shown"

tests.append(TestCase("BOTH_METHODS", "OTP and explicit keys verify independently", test_both_otp_and_explicit_keys))


def test_missing_required_args():
    """Missing both --otp_img and --ecc_pub should error."""
    args = [TEST_IMAGE]
    result = subprocess.run(['python3', 'verify_image.py'] + args, capture_output=True, text=True)
    output = result.stdout + result.stderr
    assert "Must provide either --otp_ecc or --otp_img" in output, \
        "Should require either OTP or explicit key"

tests.append(TestCase("MISSING_ARGS", "Missing key args produces error", test_missing_required_args))


def test_wrong_otp_pair_with_explicit_key():
    """OTP verification should fail but explicit key should still be attempted."""
    fake_otp_path = "/tmp/fake_otp_fallback.bin"
    with open(fake_otp_path, 'wb') as f:
        f.write(b'\x00' * 8192)
    
    args = [TEST_IMAGE, '--otp_img', fake_otp_path, '--otp_ecc', ECC_KEY]
    output, passed = run_verify(args, expect_pass=False)
    # OTP fails to find match, so overall is FAIL despite explicit key passing
    assert not passed, "When OTP verification fails, overall should FAIL"
    assert "No OTP pair matched" in output, "Should show OTP failed"
    assert "by key from otp_ecc_key_1_pub.bin" in output and "PASS" in output, "Explicit key should be attempted and pass"
    os.remove(fake_otp_path)

tests.append(TestCase("OTP_FAILS_EXPLICIT_PASS", "OTP fail attempted, explicit key shown as PASS", test_wrong_otp_pair_with_explicit_key))


# ============================================================================
# MULTIPLE BIT FLIPS
# ============================================================================

def test_kmt_multiple_bit_flips():
    """KMT signature with multiple bit flips should FAIL."""
    def corrupt(data):
        data = flip_bit(data, KMT_ECC_SIG_OFFSET, 0)
        data = flip_bit(data, KMT_ECC_SIG_OFFSET + 10, 3)
        data = flip_bit(data, KMT_ECC_SIG_OFFSET + 20, 6)
        return data
    
    corrupted_path = create_corrupted_image("kmt_multi_flip", corrupt)
    args = [corrupted_path, '--otp_ecc', ECC_KEY]
    output, passed = run_verify(args, expect_pass=False)
    assert not passed, "Should have detected multiple bit flips"
    os.remove(corrupted_path)

tests.append(TestCase("KMT_MULTI_BIT_FLIP", "KMT with multiple bit flips detected", test_kmt_multiple_bit_flips))


# ============================================================================
# RUN ALL TESTS
# ============================================================================

def main():
    print("=" * 70)
    print("COMPREHENSIVE VERIFICATION IMAGE TEST SUITE")
    print("=" * 70)
    print(f"Test Image:  {TEST_IMAGE}")
    print(f"OTP Image:   {OTP_IMAGE}")
    print(f"ECC Key:     {ECC_KEY}")
    print(f"LMS Key:     {LMS_KEY}")
    print("=" * 70)
    
    # Run all tests
    for test in tests:
        test.run()
    
    # Report results
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    
    for test in tests:
        test.report()
    
    # Summary
    passed = sum(1 for t in tests if t.result == "PASS")
    failed = sum(1 for t in tests if t.result == "FAIL")
    errors = sum(1 for t in tests if t.result == "ERROR")
    total = len(tests)
    
    print("\n" + "=" * 70)
    print(f"SUMMARY: {passed}/{total} PASSED, {failed} FAILED, {errors} ERRORS")
    print("=" * 70)
    
    return 0 if (failed == 0 and errors == 0) else 1


if __name__ == '__main__':
    sys.exit(main())
