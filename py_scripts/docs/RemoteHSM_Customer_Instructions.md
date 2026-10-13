# Remote HSM Signing Instructions for Arbel BMC TIP Firmware

## Overview
This document describes how to use the Remote HSM workflow to sign Arbel BMC firmware images with a Hardware Security Module (HSM). In this workflow:
1. **Customer runs IGPS extraction** to get unsigned binaries
2. **Customer signs** binaries with HSM (both ECC and optionally LMS)
3. **Customer runs IGPS embedding** to create final signed images
4. **Customer sends to Nuvoton**: Final signed binaries + public keys
5. **Nuvoton**: Programs OTP with customer keys, flashes images, and validates boot

**Key Concept**: Customer private keys **never leave the HSM**. Customer runs the entire build process. Only final images and public keys are sent to Nuvoton.

---

## Prerequisites

### 1. Required Components
- **IGPS Python scripts** (version 4.4.4+) - Provided by Nuvoton with all input files
- **Python 3.x** (with required dependencies)
- **Customer HSM infrastructure** capable of:
  - **ECC P-384** signing (NIST P-384/secp384r1) - **REQUIRED for all 9 binaries**
  - **LMS** signing (HSS-LMS SHA256_M32_H20) - **OPTIONAL, recommended for KMT and L0 only**

**Note**: Nuvoton provides the complete IGPS package with all necessary input files (firmware binaries, configuration, XMLs). Customer only needs to provide HSM for signing.

### 2. Keys Required

#### ECC Key (Required for all binaries)
Customer must sign **all 9 firmware binaries** with ECC P-384 key to maintain the chain of trust.
- **Curve**: NIST P-384 (secp384r1)
- **Hash**: SHA-384
- **Output**: DER-encoded signatures (~103 bytes each)
- **Private key**: Remains in customer HSM
- **Public key**: Provided to Nuvoton for OTP programming

**Critical**: All binaries must be signed with keys from the proper hierarchy:
```
OTP (customer ECC public key) 
  ↓ verifies
KMT (signed with OTP key)
  ↓ contains keys for
L0, SKMT, L1, BootBlock, BL31, OP-TEE, U-Boot
  ↓ each signed with appropriate key from KMT
```

#### LMS Key (Optional, but recommended for KMT and L0)
Post-quantum signatures for enhanced security. Recommended for critical boot components.
- **LMS Algorithm**: `LMS_SHA256_M32_H20`
- **LMOTS Algorithm**: `LMOTS_SHA256_N32_W4`
- **Hash**: SHA-512
- **Output**: Raw binary signatures (~2644 bytes each)
- **Public key**: 60 bytes, must be provided for OTP programming

**LMS Limitations**:
- Stateful (each signature updates key state)
- Limited signatures per key: 2^20 = 1,048,576
- Key rotation requires new hardware (OTP is permanent)

Example LMS key generation:
```python
from hsslms import LMS_Priv
from hsslms.utils import *

# Generate LMS key pair
priv_key = LMS_Priv(LMS_ALGORITHM_TYPE.LMS_SHA256_M32_H20, 
                    LMOTS_ALGORITHM_TYPE.LMOTS_SHA256_N32_W4)
pub_key = priv_key.gen_pub()

# Export public key (60 bytes for OTP)
pub_key_bytes = pub_key.get_pubkey()
with open("lms_public_key.bin", "wb") as f:
    f.write(pub_key_bytes)
```

---

## Workflow Steps

### Step 1: Extract Binaries for Signing

**Customer runs** the extraction command in IGPS environment:

```bash
cd <IGPS_py_scripts_directory>
python3 GenerateAll.py RemoteHSM
```

This creates **9 files** in `output_binaries/Basic/` folder:

```
output_binaries/Basic/
├── KmtAndHeader_part_to_sign.bin              # Key Manifest Table
├── TipFwAndHeader_L0_part_to_sign.bin         # TIP Firmware L0
├── SA_TipFwAndHeader_L0_part_to_sign.bin      # Standalone L0 (no SKMT)
├── SkmtAndHeader_part_to_sign.bin             # Secondary KMT
├── TipFwAndHeader_L1_part_to_sign.bin         # TIP Firmware L1
├── BootBlockAndHeader_part_to_sign.bin        # BMC Bootloader
├── BL31_AndHeader_part_to_sign.bin            # ARM Trusted Firmware
├── OpTeeAndHeader_part_to_sign.bin            # OP-TEE Secure OS
└── UbootAndHeader_part_to_sign.bin            # U-Boot Bootloader
```

**Note**: Each file contains the portion of the image that needs to be signed (starts at offset 112 of the original binary).

### Step 2: Sign All Binaries with HSM

For **each** of the 9 `*_part_to_sign.bin` files, customer generates signatures:

#### A. ECC Signature (REQUIRED for all 9 binaries)
- **Algorithm**: ECDSA with NIST P-384 curve (secp384r1)
- **Hash**: SHA-384 of the `*_part_to_sign.bin` file
- **Output Format**: DER-encoded signature (~103 bytes)
- **Naming**: Replace `_part_to_sign.bin` with `_sig.der`

Example:
```
KmtAndHeader_part_to_sign.bin → KmtAndHeader_sig.der
TipFwAndHeader_L0_part_to_sign.bin → TipFwAndHeader_L0_sig.der
SA_TipFwAndHeader_L0_part_to_sign.bin → SA_TipFwAndHeader_L0_sig.der
SkmtAndHeader_part_to_sign.bin → SkmtAndHeader_sig.der
TipFwAndHeader_L1_part_to_sign.bin → TipFwAndHeader_L1_sig.der
BootBlockAndHeader_part_to_sign.bin → BootBlockAndHeader_sig.der
BL31_AndHeader_part_to_sign.bin → BL31_AndHeader_sig.der
OpTeeAndHeader_part_to_sign.bin → OpTeeAndHeader_sig.der
UbootAndHeader_part_to_sign.bin → UbootAndHeader_sig.der
```

**All 9 ECC signatures are mandatory** to maintain the security chain of trust.

#### B. LMS Signature (OPTIONAL, recommended for KMT and L0 only)
- **Algorithm**: HSS-LMS SHA256_M32_H20 with LMOTS_SHA256_N32_W4
- **Hash**: SHA-512 of the `*_part_to_sign.bin` file
- **Output Format**: Raw binary signature (~2644 bytes)
- **Naming**: Replace `_part_to_sign.bin` with `_sig.bin`

Example (for KMT and L0 only):
```
KmtAndHeader_part_to_sign.bin → KmtAndHeader_sig.bin
TipFwAndHeader_L0_part_to_sign.bin → TipFwAndHeader_L0_sig.bin
```

**LMS Signing Steps** (if using):
1. Hash the `*_part_to_sign.bin` file with SHA-512
2. Sign the SHA-512 digest with customer LMS private key
3. Output the raw LMS signature bytes (no DER encoding)

**Summary of signature files to create**:
- **Full Security (Recommended)**: 9 `.der` files (all binaries with customer ECC keys)
- **With LMS**: 9 `.der` + 2 `.bin` files (ECC for all + LMS for KMT and L0)
- **Partial Signing (see Alternative Workflow below)**: Only critical binaries (minimum KMT + L0)

---

## Alternative Workflow: Partial Signing with Automatic Fallback

For testing or simplified workflows, customer can choose to sign **only the critical boot components** with their HSM keys. The build system will automatically use Nuvoton test keys (openssl) for unsigned components.

### When to Use Partial Signing
- **Development/Testing**: Validate HSM integration without signing all 9 binaries
- **Simplified Security Model**: Only secure the root of trust (KMT) and first-stage loader (L0)
- **Limited HSM Access**: Reduce number of HSM signing operations

⚠️ **Security Note**: Unsigned binaries will use Nuvoton's test keys, which means those components are not protected by customer keys. Only use this for testing or when the security model permits.

### Minimum Signing Requirements
Customer must provide **at minimum**:
- ✅ `KmtAndHeader_sig.der` (ECC signature for KMT)
- ✅ `TipFwAndHeader_L0_sig.der` (ECC signature for L0)
- ✅ Optional: `KmtAndHeader_sig.bin` (LMS for KMT)
- ✅ Optional: `TipFwAndHeader_L0_sig.bin` (LMS for L0)

### How Automatic Fallback Works
1. Customer signs only selected binaries (e.g., KMT and L0)
2. Customer places signature files in `output_binaries/`
3. Customer runs: `python3 GenerateAll.py RemoteHSM embed`
4. Build system:
   - Uses customer signatures for provided files
   - **Automatically signs remaining binaries with openssl (Nuvoton test keys)**
   - Completes full build successfully

### Example: Sign Only KMT and L0
```bash
# Step 1: Extract
cd <IGPS_py_scripts_directory>
python3 GenerateAll.py RemoteHSM

# Step 2: Sign only KMT and L0 with HSM
# Create these signature files:
#   - KmtAndHeader_sig.der
#   - TipFwAndHeader_L0_sig.der
#   - KmtAndHeader_sig.bin (optional LMS)
#   - TipFwAndHeader_L0_sig.bin (optional LMS)

# Step 3: Embed (remaining binaries auto-signed with openssl)
python3 GenerateAll.py RemoteHSM embed
```

Build output will show:
```
✓ Embedded signature for KmtAndHeader (customer HSM)
✓ Embedded signature for TipFwAndHeader_L0 (customer HSM)
✓ Signing TipFwAndHeader_L1 with openssl (fallback)
✓ Signing BootBlockAndHeader with openssl (fallback)
...
```

### Security Implications
| Component | If Customer Signs | If Customer Doesn't Sign |
|-----------|-------------------|--------------------------|
| KMT | Protected by customer ECC/LMS | ⚠️ Uses Nuvoton test key |
| L0 | Protected by customer ECC/LMS | ⚠️ Uses Nuvoton test key |
| SKMT, L1, BootBlock, etc. | Protected by customer ECC | Uses Nuvoton test key (chain intact but not customer-secured) |

**Recommendation**: For production deployment, sign all 9 binaries to maintain full chain-of-trust with customer keys.

---

## Standard Workflow (Full Signing)

### Step 3: Place Signatures for Embedding

**Customer must** place all signature files back in the `output_binaries/` directory (same location where extraction created the `*_part_to_sign.bin` files):

```
output_binaries/
├── KmtAndHeader_sig.der                  # ECC signature (required)
├── KmtAndHeader_sig.bin                  # LMS signature (optional)
├── TipFwAndHeader_L0_sig.der             # ECC signature (required)
├── TipFwAndHeader_L0_sig.bin             # LMS signature (optional)
├── SA_TipFwAndHeader_L0_sig.der          # ECC signature (required)
├── SkmtAndHeader_sig.der                 # ECC signature (required)
├── TipFwAndHeader_L1_sig.der             # ECC signature (required)
├── BootBlockAndHeader_sig.der            # ECC signature (required)
├── BL31_AndHeader_sig.der                # ECC signature (required)
├── OpTeeAndHeader_sig.der                # ECC signature (required)
└── UbootAndHeader_sig.der                # ECC signature (required)
```

### Step 4: Embed Signatures and Create Final Images

**Customer runs** the embedding command:

```bash
cd <IGPS_py_scripts_directory>
python3 GenerateAll.py RemoteHSM embed
```

This will:
1. Read signature files from `output_binaries/`
2. Embed signatures into the firmware binaries
3. Create final signed images in `output_binaries/Secure/`
4. Generate complete flash images

**Verify the build succeeded** - check for messages like:
```
== RemoteHSM: Embedding signatures...
✓ Embedded signature for KmtAndHeader
✓ Embedded signature for TipFwAndHeader_L0
...
```

### Step 5: Send Final Images to Nuvoton

Package and send:

**Required Files**:
- ✅ All binaries from `output_binaries/Secure/`:
  - `Kmt_TipFwL0_Skmt_TipFwL1_BootBlock_BL31_OpTee_uboot_linux.bin` (complete flash image)
  - Individual `*AndHeader.bin` files if requested
- ✅ **ECC Public Key** (DER or PEM format) for OTP programming
- ✅ **LMS Public Key** (60 bytes binary) if using LMS
- ✅ SHA-256 checksums of all files

**Do NOT send**:
- ❌ Private keys (must never leave customer HSM)
- ❌ Signature files (already embedded in binaries)
- ❌ Intermediate build files

### Step 6: Nuvoton Programs and Validates

Nuvoton will:
1. Program OTP with customer public keys (ECC and LMS if provided)
2. Flash the signed images to device
3. Validate boot and chain-of-trust
4. Provide validation results back to customer

---

## Technical Details

### Binary Structure After Signing

Each signed image has this structure:
```
Offset    Size      Content
------    ----      -------
0x00      112       Header (magic, version, lengths, key indices, etc.)
0x70      96        ECC Signature (r=48 bytes, s=48 bytes) in DER at offset
0x70+     ...       Firmware payload
...       ...       (continues to end of file)
EOF       ~2644     LMS Signature (appended, if enabled)
```

### Signature Sizes
- **ECC P-384 DER**: ~103 bytes (DER encoding of r + s, each 48 bytes)
- **LMS HSS**: ~2644 bytes (varies based on tree structure)

### File Size Changes After Signing
Example for KMT:
- Original: 512 bytes
- With ECC only: ~615 bytes (+103 bytes)
- With ECC + LMS: ~3340 bytes (+2828 bytes)

### Verification Process in ROM
1. ROM reads OTP to get customer ECC and LMS public keys
2. ROM reads KMT from flash (includes embedded signatures)
3. ROM extracts firmware payload (skips header at offset 112)
4. ROM verifies ECC signature using customer ECC public key from OTP
5. ROM verifies LMS signature (if present) using customer LMS public key from OTP
6. Both signatures must pass for KMT to be trusted
7. KMT contains keys for verifying downstream components

### Chain of Trust
```
OTP Public Keys (customer ECC + LMS keys, permanent)
    ↓ verifies
KMT (signed with OTP keys)
    ↓ contains public keys
L0 (signed with KMT key #0)
SKMT (signed with KMT key #1)
    ↓ contains public keys
L1, BootBlock, BL31, OP-TEE, U-Boot (each signed with SKMT keys)
```

**Why all 9 binaries need customer ECC signature**: If customer only signs KMT and L0, the remaining components will be signed with Nuvoton's test keys, breaking the chain of trust and defeating the purpose of remote HSM signing.

---

## Common Issues and Troubleshooting

### Issue: Signature Verification Fails
**Check**:
- ECC signature is DER format, not raw r||s bytes
- LMS signature is raw binary, not base64/hex encoded
- Hash algorithm is correct (SHA-384 for ECC, SHA-512 for LMS)
- Signature file sizes are reasonable:
  - ECC DER: 99-107 bytes (typically ~103)
  - LMS: 2640-2648 bytes (typically ~2644)
- Correct file signed (use `*_part_to_sign.bin`, not the full binary)

### Issue: Chain of Trust Broken
**Check**:
- All 9 binaries signed with customer ECC key (recommended for production)
  - If using partial signing, verify this is intentional (some components will use test keys)
- Key hierarchy maintained (KMT uses OTP key, L0 uses KMT key, etc.)
- Key indices in headers match keys used for signing
- Public keys in OTP match private keys used for signing

### Issue: L0 Fails to Boot
**Check**:
- LMS public key in OTP matches private key used for signing
- All required signatures present (ECC is mandatory, LMS optional)
- Images flashed to correct flash addresses
- Device using ROM version A3+ (for LMS support)

### Issue: LMS Signature Count Exceeded
**Check**:
- Track LMS signature counter (max 2^20 = 1,048,576)
- Never reuse LMS key state
- Generate new LMS key before exhausting current key
- Plan for key rotation before limit reached

---

## Security Notes

### Private Key Security
- **Private keys must NEVER leave customer HSM** - this is the entire purpose of RemoteHSM
- Only signatures are exchanged, never keys
- Nuvoton never has access to customer private keys

### LMS Key Management
- LMS private keys are **stateful** - each signature updates internal state
- Track signature count carefully
- Never reuse key state (would leak private key)
- Securely backup key state after each signature
- Plan for key rotation before exhausting signature count

### OTP Programming
- OTP memory is **write-once, permanent**
- Public keys cannot be changed after programming
- Key rotation requires new hardware
- Test thoroughly before OTP programming

### Signature Storage
- Store signature files securely
- Signatures prove authenticity of customer firmware
- Include signatures in version control/audit trail
- Maintain checksums for integrity verification

---

## Quick Reference

### Command Summary
```bash
# Step 1: Extract binaries for signing (Customer runs)
cd <IGPS_py_scripts_directory>
python3 GenerateAll.py RemoteHSM

# Step 2: Sign with HSM (customer creates signature files)

# Step 3: Embed signatures (Customer runs)
python3 GenerateAll.py RemoteHSM embed
```

### File Checklist
**Customer must send to Nuvoton**:
- ✅ Final signed flash images from `output_binaries/Secure/`
- ✅ ECC public key (DER or PEM format) for OTP programming
- ✅ LMS public key (60 bytes binary, if using LMS)
- ✅ SHA-256 checksums of all binary files
- 📝 Note: If using partial signing, specify which binaries are customer-signed vs. test-signed

**Nuvoton will provide back to customer**:
- ✅ Validation test results
- ✅ Boot logs showing signature verification
- ✅ OTP programming confirmation

---

## Contact Information

For questions or issues during the signing process:
- **Technical Contact**: Nuvoton Arbel BMC Team
- **Support Email**: [Your support email address]

**Please include when reporting issues**:
- Build logs with error messages
- File checksums (SHA-256) of signature files and final images
- File sizes of all signature files
- HSM model and firmware version
- Signing command/script used
- Python and IGPS version

---

## R1 | 2026-06-11 | Corrected workflow - customer runs BOTH extraction and embedding, sends final images to Nuvoton |
| 2.evision History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2026-06-11 | Updated for `embed` flag workflow, clarified all 9 binaries required, improved security notes |
| 1.0 | 2024-XX-XX | Initial version |
