#!/usr/bin/env python3
"""
ECC Key Format Converter for IGPS Integration

Converts between PEM, DER, and BIN formats for ECDSA public keys.
Designed to work with IGPS toolchain - generates output files with input base name.

Supported formats:
- PEM: Base64-encoded with ASCII armor headers
- DER: Raw binary ASN.1 encoding (X.509 SubjectPublicKeyInfo)
- BIN: Raw key coordinates with byte-reversal (Nuvoton little-endian format)

Supported curves:
- secp256r1 (P-256): 32 bytes per coordinate
- secp384r1 (P-384): 48 bytes per coordinate
- secp521r1 (P-521): 66 bytes per coordinate

Usage:
    python GenerateKeyECC_fromKnownFile.py <input_file_path>
    
Output:
    - Input: /path/to/my_key.pem → Output: my_key.der, my_key.bin
    - Input: /path/to/my_key.der → Output: my_key.pem, my_key.bin
    - Input: /path/to/my_key.bin → Output: my_key.pem, my_key.der

All output files are created in the same directory as the input file.

Author: IGPS Integration Tool
Date: 2025-11-24
"""

import sys
import os
import base64
from pathlib import Path


def parse_der_length(data, offset):
    """Parse DER length field and return (length, bytes_consumed)"""
    if data[offset] & 0x80 == 0:
        return data[offset], 1
    num_bytes = data[offset] & 0x7F
    length = 0
    for i in range(num_bytes):
        length = (length << 8) | data[offset + 1 + i]
    return length, 1 + num_bytes


def encode_der_length(length):
    """Encode an integer length value into DER format"""
    if length < 128:
        return bytes([length])
    length_bytes = []
    temp = length
    while temp > 0:
        length_bytes.insert(0, temp & 0xFF)
        temp >>= 8
    return bytes([0x80 | len(length_bytes)] + length_bytes)


def validate_pem_format(pem_content):
    """Validate PEM format. Returns (is_valid, error_message)"""
    lines = pem_content.strip().split('\n')
    
    if len(lines) < 3:
        return False, "PEM file too short (need header, data, footer)"
    
    if not lines[0].startswith('-----BEGIN'):
        return False, f"Missing BEGIN header"
    
    if not lines[-1].startswith('-----END'):
        return False, f"Missing END footer"
    
    base64_data = ''.join([line for line in lines if not line.startswith('-----')])
    
    if not base64_data:
        return False, "No Base64 data found between headers"
    
    try:
        decoded = base64.b64decode(base64_data, validate=True)
        if len(decoded) < 20:
            return False, f"Decoded data too small ({len(decoded)} bytes)"
    except Exception as e:
        return False, f"Invalid Base64 encoding: {str(e)}"
    
    return True, None


def detect_private_key_format(der_data):
    """Check if DER is a private key (SEC1 format). Returns (is_private, public_key_data)"""
    try:
        if len(der_data) < 20 or der_data[0] != 0x30:
            return False, None
            
        offset = 1
        seq_length, consumed = parse_der_length(der_data, offset)
        offset += consumed
        
        # Check for version INTEGER (value 1 for SEC1)
        if offset >= len(der_data) or der_data[offset] != 0x02:  # INTEGER tag
            return False, None
        offset += 1
        if offset >= len(der_data):
            return False, None
        version_length = der_data[offset]
        offset += 1
        if offset >= len(der_data):
            return False, None
        version = der_data[offset]
        offset += version_length
        
        if version != 1:
            return False, None
            
        # Skip the private key OCTET STRING
        if offset >= len(der_data) or der_data[offset] != 0x04:  # OCTET STRING tag
            return False, None
        offset += 1
        if offset >= len(der_data):
            return False, None
        priv_length, consumed = parse_der_length(der_data, offset)
        offset += consumed + priv_length
        
        # Look for curve OID (tagged [0]) or public key (tagged [1])
        # Skip [0] if present (0xa0 = context-specific constructed tag 0)
        if offset < len(der_data) and der_data[offset] == 0xa0:
            offset += 1
            param_length, consumed = parse_der_length(der_data, offset)
            offset += consumed + param_length
        
        # Look for the public key (usually tagged [1])
        # It's inside a context-specific tag [1] which is 0xa1
        if offset < len(der_data) and der_data[offset] == 0xa1:
            offset += 1
            pub_length, consumed = parse_der_length(der_data, offset)
            offset += consumed
            
            # Inside should be a BIT STRING with the public key
            if offset < len(der_data) and der_data[offset] == 0x03:  # BIT STRING
                offset += 1
                bitstring_length, consumed = parse_der_length(der_data, offset)
                offset += consumed
                offset += 1  # Skip the unused bits byte
                
                # Extract the public key (should start with 0x04 for uncompressed point)
                if offset + bitstring_length - 1 <= len(der_data):
                    public_key = der_data[offset:offset + bitstring_length - 1]
                    if len(public_key) > 0 and public_key[0] == 0x04:
                        return True, public_key[1:]  # Return without the 0x04 prefix
        
        return False, None
        
    except Exception as e:
        return False, None


def validate_der_format(der_data):
    """Validate DER format. Returns (is_valid, curve_name, error_message)"""
    if len(der_data) < 20:
        return False, None, f"File too small ({len(der_data)} bytes)"
    
    if der_data[0] != 0x30:
        return False, None, f"Missing SEQUENCE tag (found 0x{der_data[0]:02x})"
    
    try:
        offset = 1
        seq_length, consumed = parse_der_length(der_data, offset)
        offset += consumed
        
        if len(der_data) < offset + seq_length:
            return False, None, "File truncated"
        
        if der_data[offset] != 0x30:
            return False, None, "Missing AlgorithmIdentifier SEQUENCE"
        offset += 1
        alg_length, consumed = parse_der_length(der_data, offset)
        offset += consumed
        
        if der_data[offset] != 0x06:
            return False, None, "Missing OID tag"
        offset += 1
        oid_length = der_data[offset]
        offset += 1
        
        ec_oid = bytes([0x2a, 0x86, 0x48, 0xce, 0x3d, 0x02, 0x01])
        actual_oid = der_data[offset:offset + oid_length]
        
        if actual_oid != ec_oid:
            return False, None, f"Not an ECDSA public key"
        
        offset += oid_length
        
        if der_data[offset] != 0x06:
            return False, None, "Missing curve OID"
        offset += 1
        curve_oid_length = der_data[offset]
        offset += 1
        curve_oid = der_data[offset:offset + curve_oid_length]
        
        curve_map = {
            bytes([0x2a, 0x86, 0x48, 0xce, 0x3d, 0x03, 0x01, 0x07]): "secp256r1",
            bytes([0x2b, 0x81, 0x04, 0x00, 0x22]): "secp384r1",
            bytes([0x2b, 0x81, 0x04, 0x00, 0x23]): "secp521r1",
        }
        
        curve_name = curve_map.get(curve_oid, f"unknown")
        
        return True, curve_name, None
        
    except Exception as e:
        return False, None, f"DER parsing error: {str(e)}"


def validate_bin_format(bin_data):
    """Validate BIN format. Returns (is_valid, curve_name, error_message)"""
    if len(bin_data) % 2 != 0:
        return False, None, f"Invalid size {len(bin_data)} bytes (must be even)"
    
    coord_length = len(bin_data) // 2
    
    curve_map = {
        32: "secp256r1 (P-256)",
        48: "secp384r1 (P-384)",
        66: "secp521r1 (P-521)",
    }
    
    if coord_length not in curve_map:
        return False, None, f"Unsupported coordinate length: {coord_length} bytes"
    
    return True, curve_map[coord_length], None


def pem_to_der(pem_content):
    """Convert PEM to DER"""
    lines = pem_content.strip().split('\n')
    base64_data = ''.join([line for line in lines if not line.startswith('-----')])
    return base64.b64decode(base64_data)


def der_to_pem(der_data):
    """Convert DER to PEM"""
    base64_data = base64.b64encode(der_data).decode('ascii')
    
    lines = []
    for i in range(0, len(base64_data), 64):
        lines.append(base64_data[i:i+64])
    
    pem_content = "-----BEGIN PUBLIC KEY-----\n"
    pem_content += "\n".join(lines)
    pem_content += "\n-----END PUBLIC KEY-----\n"
    
    return pem_content


def der_to_bin(der_data):
    """Convert DER to BIN (Nuvoton little-endian format)"""
    offset = 1
    seq_length, consumed = parse_der_length(der_data, offset)
    offset += consumed + 1
    alg_length, consumed = parse_der_length(der_data, offset)
    offset += consumed + 1
    oid_length = der_data[offset]
    offset += 1 + oid_length + 1
    curve_oid_length = der_data[offset]
    offset += 1 + curve_oid_length + 1
    bitstring_length, consumed = parse_der_length(der_data, offset)
    offset += consumed + 1
    
    key_data = der_data[offset:offset + bitstring_length - 1]
    
    if key_data[0] != 0x04:
        raise ValueError(f"Missing uncompressed point indicator (got 0x{key_data[0]:02x})")
    
    key_data = key_data[1:]
    
    coord_length = len(key_data) // 2
    x_coord = key_data[:coord_length]
    y_coord = key_data[coord_length:]
    
    # Nuvoton format: reverse both coordinates (little-endian)
    return x_coord[::-1] + y_coord[::-1]


def bin_to_der(bin_data):
    """Convert BIN to DER"""
    coord_length = len(bin_data) // 2
    
    curve_map = {
        32: bytes([0x2a, 0x86, 0x48, 0xce, 0x3d, 0x03, 0x01, 0x07]),  # P-256
        48: bytes([0x2b, 0x81, 0x04, 0x00, 0x22]),                    # P-384
        66: bytes([0x2b, 0x81, 0x04, 0x00, 0x23]),                    # P-521
    }
    
    curve_oid = curve_map[coord_length]
    
    # Reverse coordinates (little-endian to big-endian)
    x_coord = bin_data[:coord_length][::-1]
    y_coord = bin_data[coord_length:][::-1]
    
    key_point = bytes([0x04]) + x_coord + y_coord
    
    bitstring = bytes([0x03]) + encode_der_length(len(key_point) + 1) + bytes([0x00]) + key_point
    
    ec_oid = bytes([0x06, 0x07, 0x2a, 0x86, 0x48, 0xce, 0x3d, 0x02, 0x01])
    curve_oid_enc = bytes([0x06, len(curve_oid)]) + curve_oid
    
    alg_id = bytes([0x30]) + encode_der_length(len(ec_oid) + len(curve_oid_enc)) + ec_oid + curve_oid_enc
    
    outer = bytes([0x30]) + encode_der_length(len(alg_id) + len(bitstring)) + alg_id + bitstring
    
    return outer


def process_file(input_path):
    """
    Main conversion function.
    Converts input file to the other two formats using the same base name.
    """
    input_path = Path(input_path).resolve()
    
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return False
    
    extension = input_path.suffix.lower()
    base_name = input_path.stem
    output_dir = input_path.parent
    is_private_key_input = False
    
    print(f"Input file: {input_path}")
    print(f"Base name: {base_name}")
    print(f"Size: {input_path.stat().st_size} bytes")
    print()
    
    conversions = {
        ".pem": {
            "read_mode": 'r',
            "loader": lambda f: f.read(),
            "validator": validate_pem_format,
            "to_der": pem_to_der,
            "outputs": [
                ('.der', lambda pem: pem_to_der(pem), 'wb'),
                ('.bin', lambda pem: der_to_bin(pem_to_der(pem)), 'wb')
            ]
        },
        ".der": {
            "read_mode": 'rb',
            "loader": lambda f: f.read(),
            "validator": validate_der_format,
            "to_der": lambda x: x,
            "outputs": [
                ('.der', lambda x: x, 'wb'),
                ('.pem', der_to_pem, 'w'),
                ('.bin', der_to_bin, 'wb')
            ]
        },
        ".bin": {
            "read_mode": 'rb',
            "loader": lambda f: f.read(),
            "validator": validate_bin_format,
            "to_der": bin_to_der,
            "outputs": [
                ('.der', bin_to_der, 'wb'),
                ('.pem', lambda bin_data: der_to_pem(bin_to_der(bin_data)), 'w')
            ]
        }
    }
    
    if extension not in conversions:
        print(f"Error: Unsupported file extension '{extension}'")
        print("Expected: .pem, .der, or .bin")
        return False
    
    try:
        config = conversions[extension]
        
        with open(input_path, config["read_mode"]) as f:
            input_data = config["loader"](f)
        
        validation_result = config["validator"](input_data)
        if extension == ".pem":
            is_valid, error = validation_result
            curve_name = None
        else:
            is_valid, curve_name, error = validation_result
        
        if not is_valid and extension == ".der":
            is_private, public_key_coords = detect_private_key_format(input_data)
            if is_private and public_key_coords:
                print(f"Detected private key format - extracting public key")
                is_private_key_input = True
                coord_length = len(public_key_coords) // 2
                curve_map = {
                    32: bytes([0x2a, 0x86, 0x48, 0xce, 0x3d, 0x03, 0x01, 0x07]),  # P-256
                    48: bytes([0x2b, 0x81, 0x04, 0x00, 0x22]),                    # P-384
                    66: bytes([0x2b, 0x81, 0x04, 0x00, 0x23]),                    # P-521
                }
                if coord_length in curve_map:
                    input_data = bin_to_der(public_key_coords[:coord_length][::-1] + public_key_coords[coord_length:][::-1])
                    is_valid, curve_name, error = validate_der_format(input_data)
                    if is_valid:
                        print(f"Valid ECDSA public key extracted (curve: {curve_name})")
                    else:
                        print(f"Error: Could not extract valid public key: {error}")
                        return False
                else:
                    print(f"Error: Unsupported key size in private key")
                    return False
            else:
                print(f"Error: Invalid {extension[1:].upper()} format: {error}")
                return False
        elif not is_valid:
            print(f"Error: Invalid {extension[1:].upper()} format: {error}")
            return False
        
        success_msg = f"Valid {extension[1:].upper()} format"
        if curve_name:
            success_msg += f" (curve: {curve_name})"
        print(success_msg)
        
        der_data = config["to_der"](input_data)
        
        if extension != ".der":
            is_valid, curve_name, error = validate_der_format(der_data)
            if not is_valid:
                print(f"Error: Invalid DER content: {error}")
                return False
            if extension == ".pem":
                print(f"Valid ECDSA public key (curve: {curve_name})")
        
        print()
        print("Conversion successful!")
        print()
        
        for out_ext, converter, mode in config["outputs"]:
            if extension == ".der" and out_ext == ".der" and not is_private_key_input:
                continue
            if is_private_key_input:
                output_path = output_dir / f"{base_name}_pub{out_ext}"
            else:
                output_path = output_dir / f"{base_name}{out_ext}"
            output_data = converter(input_data)
            
            with open(output_path, mode) as f:
                f.write(output_data)
            
            print(f"Created: {output_path} ({len(output_data)} bytes)")
        
        return True
        
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) != 2:
        print("ECC Key Format Converter for IGPS")
        print()
        print("Usage: python GenerateKeyECC_fromKnownFile.py <input_file_path>")
        print()
        print("Converts between PEM, DER, and BIN formats:")
        print("  Input: .pem → Output: .der and .bin")
        print("  Input: .der → Output: .pem and .bin")
        print("  Input: .bin → Output: .pem and .der")
        print()
        print("Output files use the same base name as input.")
        print("Example: my_key.pem → my_key.der, my_key.bin")
        print()
        print("Supported curves: P-256, P-384, P-521")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    print("="*70)
    print("ECC KEY FORMAT CONVERTER")
    print("="*70)
    print()
    
    success = process_file(input_file)
    
    print()
    print("="*70)
    
    if success:
        print("All conversions completed successfully!")
        sys.exit(0)
    else:
        print("Conversion failed - see errors above")
        sys.exit(1)


if __name__ == "__main__":
    main()
