# verify_image.py — NPCM TIP Image Verification Tool

Verifies the integrity and authenticity of IGPS-generated signed binary images.
Supports composite images containing a KMT (Key Manifest Table) section and an L0 (TIP FW) section.

---

## Usage

```
python3 verify_image.py IMAGE [--otp_img OTP_IMG_MAP_BIN] [--otp_ecc OTP_ECC_PUB_BIN] [--otp_lms OTP_LMS_PUB_BIN]
                               [--kmt_ecc KMT_ECC_PUB_BIN] [--kmt_lms KMT_LMS_PUB_BIN]
```

### Positional argument

| Argument | Description |
|----------|-------------|
| `IMAGE`  | **Required.** Path to the binary image to verify (e.g., `Kmt_TipFwL0.bin`). |

### Optional arguments

| Flag | Description |
|------|-------------|
| `--otp_img OTP_IMG_MAP_BIN` | Path to OTP fuse map binary (e.g., `arbel_fuse_map.bin`). Tries all 9 OTP key pairs automatically. If used, `--otp_ecc` and `--otp_lms` are not required. |
| `--otp_ecc OTP_ECC_PUB_BIN` | Path to OTP ECC public key binary that signs the KMT section (96 bytes, P-384 x\|\|y little-endian). Optional since can be verified by `--otp_img`. |
| `--otp_lms OTP_LMS_PUB_BIN` | Path to OTP LMS public key binary that signs the KMT section (56 bytes). Optional since can be verified by `--otp_img`. |
| `--kmt_ecc KMT_ECC_PUB_BIN` | Path to KMT ECC public key that signs the L0/TFT section (96 bytes). Optional since verifies in addition to the key auto-extracted from the KMT payload. |
| `--kmt_lms KMT_LMS_PUB_BIN` | Path to KMT LMS public key that signs the L0/TFT section (56 bytes). Optional since verifies in addition to the key auto-extracted from the KMT payload. |

**At least one of `--otp_img` or `--otp_ecc` must be provided.**  
`--otp_img` and `--otp_ecc`/`--otp_lms` are **independent** — both run when both are given.

---

## What is verified

### KMT section (`0x0000..0x0FFF`)

| Check | Algorithm | Coverage |
|-------|-----------|----------|
| CRC32 | Custom CRC32 (init=0, poly=0xEDB88320, no final XOR) | `image[0x70 .. 0x100 + fw_length)` |
| ECC Signature | ECDSA P-384 + SHA-512 | Same range as CRC |
| LMS Signature | LMS-SHA256-M32-H20 + LMOTS-SHA256-N32-W4 | SHA-512 digest of same range |

### L0 / TIP FW section (`0x1000..end`, composite images only)

Same three checks are applied, using keys extracted from the KMT payload (or supplied via `--kmt_ecc`/`--kmt_lms`).

---

## Verification summary output

Each check is reported individually in the summary:

```
============================================================
Verification Summary
============================================================
KMT verification:
  KMT CRC32 inside Kmt_TipFwL0.bin                                              PASS
  KMT ECC Signature by key from arbel_fuse_map.bin OTP pair 1 (starting from 0) PASS
  KMT LMS Signature by key from arbel_fuse_map.bin OTP pair 1 (starting from 0) PASS
  KMT ECC Signature by key from otp_ecc_key_1_pub.bin                           PASS
  KMT LMS Signature by key from otp_lms_key_1_pub.bin                           PASS
L0 (TFT) verification:
  L0 CRC32 inside Kmt_TipFwL0.bin                                               PASS
  L0 ECC Signature by key from Kmt_TipFwL0.bin KMT payload, index 0             PASS
  L0 LMS Signature by key from Kmt_TipFwL0.bin KMT payload, index 0             PASS
============================================================
OVERALL: PASS
```

---

## Examples

### 1. Verify using OTP fuse map (auto-try all 9 key pairs)

The tool reads `arbel_fuse_map.bin`, extracts all 9 ECC+LMS key pairs, and tries each until one verifies both signatures.

```bash
python3 verify_image.py \
    ImageGeneration/output_binaries/Secure/Kmt_TipFwL0.bin \
    --otp_img ImageGeneration/output_binaries/Secure/arbel_fuse_map.bin
```

---

### 2. Verify using explicit OTP key files

Provide the exact key pair used to sign the image.

```bash
python3 verify_image.py \
    ImageGeneration/output_binaries/Secure/Kmt_TipFwL0.bin \
    --otp_ecc ImageGeneration/keys/openssl/otp_ecc_key_1_pub.bin \
    --otp_lms ImageGeneration/keys/openssl/otp_lms_key_1_pub.bin
```

---

### 3. Verify using explicit ECC only (skip LMS)

When LMS key is unavailable or LMS verification is not required.

```bash
python3 verify_image.py \
    ImageGeneration/output_binaries/Secure/Kmt_TipFwL0.bin \
    --otp_ecc ImageGeneration/keys/openssl/otp_ecc_key_1_pub.bin
```

---

### 4. Verify with both OTP fuse map and explicit keys (independent)

Both verification paths run independently. Useful to cross-validate the fuse map content against known key files.

```bash
python3 verify_image.py \
    ImageGeneration/output_binaries/Secure/Kmt_TipFwL0.bin \
    --otp_img ImageGeneration/output_binaries/Secure/arbel_fuse_map.bin \
    --otp_ecc ImageGeneration/keys/openssl/otp_ecc_key_1_pub.bin \
    --otp_lms ImageGeneration/keys/openssl/otp_lms_key_1_pub.bin
```

---

### 5. Verify KMT-only image (no L0 section)

Works on standalone KMT binaries. L0 verification is skipped automatically if no L0 section is present.

```bash
python3 verify_image.py \
    ImageGeneration/output_binaries/Secure/kmt_map.bin \
    --otp_img ImageGeneration/output_binaries/Secure/arbel_fuse_map.bin
```

---

### 6. Verify L0 section with explicit KMT keys

The KMT keys used to sign L0 are always auto-extracted from the KMT payload.
Use `--kmt_ecc`/`--kmt_lms` to additionally verify with known key files — both results are reported independently.

```bash
python3 verify_image.py \
    ImageGeneration/output_binaries/Secure/Kmt_TipFwL0.bin \
    --otp_img ImageGeneration/output_binaries/Secure/arbel_fuse_map.bin \
    --kmt_ecc ImageGeneration/keys/openssl/kmt_ecc_key_0_pub.bin \
    --kmt_lms ImageGeneration/keys/openssl/kmt_lms_key_0_pub.bin
```

Expected summary will include both `L0 ECC Signature by key from Kmt_TipFwL0.bin KMT payload, index 0` and `L0 ECC Signature by key from kmt_ecc_key_0_pub.bin`.

---

## Image layout reference

```
Offset      Size    Description
──────────────────────────────────────────────────────────────────
0x0000        4     Anchor = 0x2A3B4D5E
0x0004        4     Extended anchor / CRC enable flag
0x000C        4     CRC32 (custom, no XOR, over [0x70..0x100+fw_length))
0x0010       96     ECC signature: r_LE (48B) || s_LE (48B)
0x0070      var     ── Signed/CRC'd data starts here ──
                    SPI config, fw_start_addr, fw_length, key indices,
                    LMS flags, timestamps, etc.
0x0100      var     KMT payload (kmt_map.bin: public key slots)
                    Size = fw_length field at 0x84
                    ECC slots: index * 96 bytes from payload start
                    LMS slots: 0x100 + index * 0x50 from payload start
0x0100+fw   var     LMS signature (if enabled), 32-byte aligned
               …    0xFF padding to 0x1000 boundary
──────────────────────────────────────────────────────────────────
0x1000      var     L0 / TIP FW section (composite images only)
                    Same header structure as KMT
```

---

## Key file formats

| File | Size | Format |
|------|------|--------|
| OTP ECC public key (`--otp_ecc`) | 96 bytes | P-384: `x_LE` (48B) \|\| `y_LE` (48B) |
| OTP LMS public key (`--otp_lms`) | 56 bytes | LMS public key structure (type + I + K) |
| OTP fuse map (`--otp_img`) | variable | `arbel_fuse_map.bin` as generated by IGPS |
| KMT ECC key (`--kmt_ecc`) | 96 bytes | Same format as OTP ECC key; used for additional L0 verification |
| KMT LMS key (`--kmt_lms`) | 56 bytes | Same format as OTP LMS key; used for additional L0 verification |

---

## Exit codes

| Code | Meaning |
|------|---------|
| `0`  | All requested verifications passed |
| `1`  | One or more verifications failed, or argument/file error |

---

## Dependencies

```bash
pip install cryptography hsslms
```

| Package | Purpose |
|---------|---------|
| `cryptography` | ECDSA P-384 signature verification |
| `hsslms` | LMS-SHA256-M32-H20 / LMOTS-SHA256-N32-W4 verification |

---

## Running the test suite

```bash
cd igps/py_scripts
python3 test_verify_image.py
```

The test suite covers:
- Baseline verification (OTP, explicit keys, both simultaneously)
- KMT ECC/LMS signature tampering (single bit flips, multi-bit flips)
- KMT payload corruption
- KMT header field tampering (`fw_length`)
- L0 payload, ECC signature, and `fw_length` corruption
- Wrong key files and wrong OTP fuse map
- Image truncation
- All flag scenarios and combinations
