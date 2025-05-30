# SPDX-License-Identifier: GPL-2.0
#
# Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
#
# Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
#-------------------------------------------------------------------------

import sys
import os
import hashlib
import pickle
# This file was downloaded from :https://github.com/andrivet/python-asn1/blob/master/src/asn1.py with MIT license:
try:
	from . import asn1
except: 
	import asn1
	
import binascii
from array import array
linux_prefix = " "
openssl = "openssl"

key_size = 48
ecc_type = "384"


def  BigNum_2_Array(num, size, print_it):
	arr = bytearray(size)
	for ind in range(size):
		arr[ind] = (num >> (ind*8) ) & 255
	if (print_it):
		res = "-".join(format(x, '-02X') for x in arr)
		print(("arr:  " + res))
		print(("Size: " + str(size)))
	return arr
	
def  Array_2_BigNum(arr, size, print_it):
	num = 0
	for ind in range(size):
		num = num + ((arr[ind] & 0xFF) << (ind*8) )
	if (print_it):	
		print(("Val:  " + str(hex(num))))
		print(("Size: " + str(size)))
	return num

# 
def  _Asn1_get_bins_from_DER(decoder, int_val, cnt):
	while not decoder.eof():
		tag = decoder.peek()
		if tag.typ == asn1.Types.Primitive:
			tag, int_bn = decoder.read()
			#print(' ' * cnt + '[{}] {}: {}\n'.format(class_id_to_string(tag.cls),tag_id_to_string(tag.nr), value_to_string(tag.nr, int_bn)))

			# private and public key comes in a BitString format. 
			# Public starts with [0x00,0x04] which should be ommitted, and then 
			# 48 bytes of X and 48 bytes of Y element of public key.
			# Note: the public key is a spot on the eliptic curve,
			# so it can be verified as a valid point
			if((tag.nr  == asn1.Numbers.BitString) or (tag.nr  == asn1.Numbers.OctetString)) :
				int_value = bytearray(int_bn)
				
				# trim the extra 2 bytes from the public. 
				# Why are they there? I don't know:
				int_bn_size = len(int_bn)
				
				
				# if it's a private key, reverse the array:
				# if (key_size == int_bn_size):
				# 	int_value = int_value[::-1]
				# if (key_size < int_bn_size):
				# int_value = int_value[::-1]
				
				# convert to BigNum:
				int_val[cnt] = Array_2_BigNum(int_value, int_bn_size, True)
				cnt = cnt + 1
				
			if((tag.nr  == asn1.Numbers.Integer) and (int_bn != 1)):
				print((" Int = " + str(hex(int_bn))))
				int_val[cnt] = int_bn	
				cnt = cnt + 1
				
		elif tag.typ == asn1.Types.Constructed:
			#print(' ' * cnt + '[{}] {}\n'.format(class_id_to_string(tag.cls), tag_id_to_string(tag.nr)))
			decoder.enter()
			_Asn1_get_bins_from_DER(decoder, int_val, cnt)
			decoder.leave()
	



# all the DER files we have contain 2 BN (signed integers)
def  Asn1_get_bins_from_DER(keyDER, int_val):
	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	bin_file = open(keyDER, "rb")
	key_array = bin_file.read()
	bin_file.close()	
	os.chdir(currpath)
	
	decoder = asn1.Decoder()
	decoder.start(key_array)
	
	cnt = 0

	_Asn1_get_bins_from_DER(decoder, int_val, cnt)

class OpensslError(Exception):

	def __init__(self, value):
		self.strerror = "Openssl error value:" + str(value)
	def __str__(self):
		return repr(self.strerror)


def  Extract_bin_public_key_from_DER_file(DER_file, bin_file, includingPriv = 1 ):
	print(("\nExtract binary public key %s from %s " % (bin_file, DER_file)))
	# a list of byte arrays of the prv and pub:
	prvKey = 0
	pubKey = 0
	if includingPriv !=  0:
		keyBin = [prvKey , pubKey]
	else:
		keyBin = [pubKey]

	Asn1_get_bins_from_DER(DER_file, keyBin)

	keyBinPubLocation = 0
	if includingPriv != 0:
		print ("\nPrivate Key:")
		arr_prv = BigNum_2_Array(keyBin[0], key_size, True)
		keyBinPubLocation = 1

	print ("\nPublic Key:")
	arr_pub = BigNum_2_Array(keyBin[keyBinPubLocation], key_size * 2 + 2, True)
	
	#remove last 2 bytes:
	arr_pub = arr_pub[2:]
	
	res = "-".join(format(x, '-02X') for x in arr_pub)
	print(("public:  " + res))
	
	
	# and reverse:
	arr_pub_x = arr_pub[0:(key_size)]
	arr_pub_y = arr_pub[key_size:] 
	arr_pub = arr_pub_x[::-1] + arr_pub_y[::-1]
	
	res = "-".join(format(x, '-02X') for x in arr_pub)
	print(("public:  " + res))
	res = "-".join(format(x, '-02X') for x in arr_pub_x)
	print(("public X:  " + res))
	res = "-".join(format(x, '-02X') for x in arr_pub_y)
	print(("public Y:  " + res))

	# save public key bin
	bin_file_handler = open(bin_file , "wb")
	bin_file_handler.write(arr_pub)
	bin_file_handler.close()

def executeCMD(cmd):
	cmd_to_print = cmd
	pincode = cmd.find("-p ")
	if pincode > 0 :
		cmd_to_print = cmd[0:(pincode + 2)] + "****** " + cmd[(pincode + 10):]
	print(cmd_to_print)
	rc = os.system(cmd)
	if rc != 0:
		raise ValueError("execute CMD failed \n\n")
		
def extract_bin_file_to_sign(bin_filename, begin_offset):
	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	bin_file_to_sign = bin_filename.replace(".", "_part_to_sign.")
	# read input file:
	if (os.path.isfile(bin_filename) == False):
		print("Input file " + bin_filename + " is missing")
		raise Exception('Missing file')
	bin_file = open(bin_filename, "rb")
	input = bin_file.read()
	bin_file.close()
	# build temporary file starting from the desired offset of the binfile
	bin_file = open(bin_file_to_sign , "wb")
	bin_file.write(input[begin_offset::])
	bin_file.close()

def Sign_binary_openssl_or_HSM(bin_filename, begin_offset, key, embed_signature, output_filename , TypeOfKey, pinCode, idNum, isECC, isLMS ,lms_key):
	_openssl = openssl
	_pkcs_tool = "pkcs11-tool.exe"
	if os.name != "nt":
		_openssl = linux_prefix + openssl
		_pkcs_tool = linux_prefix + "pkcs11-tool"

	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	
	if (os.path.isfile(bin_filename) == False):
		print(("currpath " +  os.getcwd()))
		print(("\033[91m" + "Sign_binary   Error: " +  bin_filename + " file is missing\n\n" + "\033[97m"))
		return -1


	try:
		bin_file_to_sign = bin_filename.replace(".", "_part_to_sign.")
		bin_file_to_sign_hashed = ""
		sig_der = output_filename.replace(".bin", "_sig.der")
		
		# read input file:
		if (os.path.isfile(bin_filename) == False):
			print(("\033[91m" + "Input file " + bin_filename + " is missing" + "\033[97m"))
			raise Exception('Missing file')
		bin_file = open(bin_filename, "rb")
		input = bin_file.read()
		bin_file.close()
		
		begin_offset = int(begin_offset)
		# build temporary file starting from the desired offset of the binfile
		bin_file = open(bin_file_to_sign , "wb")
		bin_file.write(input[begin_offset::])
		bin_file.close()
		if (isECC == True):
			pub_key_der = key.replace(".der", "_pub.der", 1)
			if (TypeOfKey == "openssl"):
			################################################################################
				sig_der = output_filename.replace(".bin", "_sig.der")
			# call openssl to generate a signature
				cmd = "%s dgst -sha512 -keyform der -sign \"%s\" \"%s\" > \"%s\"" \
				% (_openssl, key, bin_file_to_sign, sig_der)
			
				if (os.path.isfile(key) == False):
					print(("currpath " +  os.getcwd()))
					print(("\033[91m" + "Sign_binary   Error: " +  key + " key file is missing\n\n" + "\033[97m"))
					return -1
				
				if (os.path.isfile(bin_file_to_sign) == False):
					print(("currpath " +  os.getcwd()))
					print(("\033[91m" + "Sign_binary   Error: " +  bin_file_to_sign + " file is missing\n\n" + "\033[97m"))
					return -1
				
				executeCMD(cmd)
			

				print("verify:")
				cmd = "%s dgst -sha512 -keyform der -verify \"%s\" -signature \"%s\" \"%s\" " \
					  % (_openssl, pub_key_der, sig_der, bin_file_to_sign)
				executeCMD(cmd)

			else: #HSM

				sig_der = output_filename.replace(".bin", "_HSM.sig")
			#hash the big data first
				bin_file_to_sign_hashed = bin_file_to_sign.replace(".bin", "_hashed.bin")
				print(("bin_file_to_sign_hashed is:"+bin_file_to_sign_hashed))

				cmd = _pkcs_tool + " --id " + idNum + " --hash -m SHA512  -p " + pinCode + " -i " + bin_file_to_sign + " --output-file " + bin_file_to_sign_hashed
				executeCMD(cmd)

				cmd = _pkcs_tool + " --id " + idNum + " -s -p " + pinCode + " -m ECDSA --signature-format openssl -i " + bin_file_to_sign_hashed + " --output-file " + sig_der
				executeCMD(cmd)

				print("verify:")
				cmd = "%s dgst -sha512 -keyform der -verify %s -signature %s %s " \
					  % (_openssl, pub_key_der, sig_der, bin_file_to_sign)
				executeCMD(cmd)


		#joined code for open SSL and HSM
			s = 0
			r = 0
			signature = [r, s]
			print(("sig_der is: " + sig_der))
			Asn1_get_bins_from_DER(sig_der, signature)
			print ("\nSignature.r:")
			arr_r = BigNum_2_Array(signature[0], key_size, True)
			print ("\nSignature.s:")
			arr_s = BigNum_2_Array(signature[1], key_size, True)

			embed_signature = int(embed_signature)
			output = input[:embed_signature] + arr_r + arr_s + input[(embed_signature + key_size*2):]

		if (isLMS == True):
			if (TypeOfKey == "openssl"):
				bin_file_to_sign_hashed = bin_file_to_sign.replace(".bin", "_hashed.bin")
				print("\033[95m" + "bin_file_to_sign is " + bin_file_to_sign)
				sig_binary = output_filename.replace(".bin", "_sig.bin")
				public_pickled_bin_file = lms_key.replace(".bin" , "_pickled_pub.bin")
				private_pickled_bin_file = lms_key.replace(".bin", "_pickled_priv.bin")
				print("private_pickled_bin_file is " + private_pickled_bin_file)
				print("public_pickled_bin_file is " + public_pickled_bin_file)
			
				# Deserialize the updated private key + public key from file
				with open(private_pickled_bin_file, 'rb') as f:
					priv_key_loaded = pickle.load(f)
				with open(public_pickled_bin_file, 'rb') as f:
					pub_key_loaded = pickle.load(f)
				#sha 512 the input image and save it before signing it
				cmd = "%s dgst -sha512 -binary -out \"%s\" \"%s\"" \
				% (_openssl, bin_file_to_sign_hashed, bin_file_to_sign)
				executeCMD(cmd)
				
				with open(bin_file_to_sign_hashed, "rb") as file:
					buffer = file.read()
				# private key is signing the bin_file_to_sign
				signature = priv_key_loaded.sign(buffer)
				
				# verify the signature, if invalid an exception will be raised
				try:
					pub_key_loaded.verify(buffer, signature)
					print("LMS Signature is valid. "+"\x1b[0m")

				except Exception as e:
					print(f"LMS sig verification failed: {e}")
					print("Exception details:", e)
				
				output_file = open(sig_binary, "w+b")
				output_file.write(signature)
				output_file.close()
				
			#else: #HSM ---TODO --
			#concatante the signature to the footer of the output image	
			output = output + signature	
		#
		# shared code for ECC and LMS:
		#
		# write the input with the embedded signature to the output file
		print(("write to output file " + output_filename))
		output_file = open(output_filename, "w+b")
		output_file.write(output)
		output_file.close()
	
		# Ensure output is aligned to 32 bytes
		padding_length = 32 - (len(output) % 32)
		if padding_length != 32:
			output += b'\x00' * padding_length

		output_file = open(output_filename, "w+b")
		output_file.write(output)
		output_file.close()
		
	finally:
		if os.path.isfile(sig_der)  :
			os.remove(sig_der)
		if os.path.isfile(bin_file_to_sign):
			os.remove(bin_file_to_sign)
		if os.path.isfile(bin_file_to_sign_hashed):
			os.remove(bin_file_to_sign_hashed)

		os.chdir(currpath)



def bin_calc_hash(bin_filename, max_size):
	_openssl = openssl
	if os.name != "nt":
		_openssl = linux_prefix + openssl

	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	
	if (os.path.isfile(bin_filename) == False):
		print(("currpath " +  os.getcwd()))
		print(("\033[91m" + "bin_calc_hash  Error: " +  bin_filename + " file is missing\n\n" + "\033[97m"))
		return -1

	try:
		h = hashlib.new("sha256")
		with open(bin_filename,"rb") as f:
			h.update(f.read())

	finally:
		os.chdir(currpath)
		
	arr = bytearray(h.digest())
	
	arr_ret = arr[:max_size]
	# hex_str = ''.join(['{:02x}'.format(byte) for byte in arr_ret])
	# print(hex_str)
	return arr_ret
	
def Embed_external_sig(sig_der, sig_bin_lms, input_file, output_file, embed_signature, isLMS=False):
	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	
	print(("\033[95m" + "=========================================================="))
	print(("== Embed external sig ECC: %s to %s    " % (sig_der, input_file)))
	if isLMS:
		print(("== Embed external sig LMS: %s    " % (sig_bin_lms)))
	print(("==========================================================" + "\x1b[0m"))

	try:
		# read input file:
		if (os.path.isfile(input_file) == False):
			print(("\033[91m" + "Embed_external_sig: input file " + input_file + " is missing\n\n" + "\033[97m"))
			raise Exception('Missing file')
		
		if (os.path.isfile(sig_der) == False):
			print(("\033[91m" + "Embed_external_sig: ECC sig file " + sig_der + " is missing\n\n" + "\033[97m"))
			raise Exception('Missing file')
		
		if isLMS:
			if (os.path.isfile(sig_bin_lms) == False):
				print(("\033[91m" + "Embed_external_sig: LMS sig file " + sig_bin_lms + " is missing\n\n" + "\033[97m"))
				raise Exception('Missing file')
		
		bin_file = open(input_file, "rb")
		input = bin_file.read()
		bin_file.close()

		# get the generated ECC signature and embed it in the input binary
		s = 0
		r = 0
		signature = [r, s]
		
		print("DER => bin")
		Asn1_get_bins_from_DER(sig_der, signature)
		
		print ("\nSignature.r:")
		arr_r = BigNum_2_Array(signature[0], key_size, True)
		print(("size of arr_r " + str(len(arr_r))))
		
		print ("\nSignature.s:")
		arr_s = BigNum_2_Array(signature[1], key_size, True)
		print(("size of arr_s " + str(len(arr_s))))
		
		print(("size of input " + str(len(input))))
		output = input[:embed_signature] + arr_r + arr_s + input[(embed_signature + key_size*2):]

		# Process LMS signature as binary and concatenate at the end if isLMS is True
		if isLMS:
			with open(sig_bin_lms, "rb") as sig_file:
				signature_lms = sig_file.read()
			print("LMS Signature size: ", len(signature_lms))

			output += signature_lms

		# write the input with the embedded signature(s) to the output file
		print(("write to output file " + output_file))
		output_file = open(output_file, "w+b")
		output_file.write(output)
		output_file.close()
	except:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print(("\n\n Embed_external_sig.py: embed external key %s to %s failed" % (input_file, output_file)))
		raise Exception('Embed_external_sig')
	finally:
		os.chdir(currpath)

# Replace_binary_single_byte: used to embed the key index inside the image. usually at offset 0x140.
def Replace_binary_single_byte(binfile, offset, value, read_modify_write = 0):
	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	print(("**** Insert %s offset %s value %s RMW %s****" % (binfile, hex(int(offset)), hex(int(value)), str(read_modify_write))))
	try:
		if (os.path.isfile(binfile) == False):
			print(("currpath " +  os.getcwd()))
			print(("\033[91m" + "Replace_binary_single_byte   Error: " +  binfile + " file is missing\n\n" + "\033[97m"))
			return -1
			
		with open(binfile, 'rb+') as f:
			f.seek(int(offset))
			val = int(value)
			if (read_modify_write == 1):
				val = f.read(1)[0]
				val = val | value
				f.seek(int(offset))
			print("   Writing %s" % hex(val))
			f.write((chr(int(val))).encode('utf8'))
		
		f.close()
		
	except:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print(("\n\n FAIL %s Replace_binary_single_byte.py: file %s offset %s array %s	" % (binfile, str(offset), str(value), str(read_modify_write))))
		raise Exception('Replace_binary_single_byte')
	finally:
		os.chdir(currpath)


# Replace_binary_array: used to embed an array inside an image. Used for timestamp and address pointers.
# bArray=True: num is an array, just write it in the file
# bArray=False: num is a number in little endian, convert to array
# update_current_val = if it is true , the script will use "|" that will update and not replace entirely the existing value
def Replace_binary_array(input_file, offset, num, size, bArray, title, update_current_val=False):
	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	print("\033[95m==========================================================")
	print(("== %s Replace_binary_array file %s offset %s " % (title, input_file, hex(offset))))
	print("==========================================================\x1b[0m")

	try:
		# read input file:
		if (os.path.isfile(input_file) == False):
			print(("\033[91m" + "Replace_binary_array: input file " + input_file + " is missing\n\n" + "\033[97m"))
			raise Exception('Missing file')

		bin_file = open(input_file, "rb")
		input_data = bytearray(bin_file.read())  # Change input -> input_data to match the original style
		bin_file.close()

		if (bArray == True):
			arr1 = BigNum_2_Array(num, size, True)
		else:
			if isinstance(num, int):
				arr1 = num.to_bytes(size, "little")  # Convert int to bytes (little-endian)
			elif isinstance(num, bytes):
				arr1 = num  # Use bytes directly
			else:
				raise TypeError("num should be an int or bytes, but got " + str(type(num)))

		# pad with zeros if needed or truncate array if needed
		if len(arr1) < size:
			arr = b'\x00' * (size - len(arr1)) + arr1	
		elif len(arr1) > size:
			arr = arr1[:size]	
		else:
			arr = arr1

		if update_current_val:
			# Perform bitwise OR with existing data
			existing_data = input_data[offset:offset + size]
			existing_data = existing_data.ljust(size, b'\x00')  # Ensure correct size
			arr = bytes(a | b for a, b in zip(existing_data, arr))

		hex_string = ''.join(['{:02x}'.format(byte) for byte in arr])
		
		#print(("size of input " + str(len(input_data))))
		output = input_data[:offset] + arr + input_data[(offset + size):]
		
		# write the input with the embedded signature to the output file
		print("write " + hex_string + " to file " + input_file)
		input_file = open(input_file, "w+b")
		input_file.write(output)
		input_file.close()
	except:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print(("\n\n FAIL %s Replace_binary_array.py: file %s offset %s array %s	" % (title, input_file, str(offset), str(arr))))
		raise Exception('Replace_binary_array')

	finally:
		os.chdir(currpath)



	
def Sign_binary(binfile, begin_offset, key, embed_signature, outputFile, TypeOfKey, pinCode , idNum ,isECC, isLMS, lms_key):

	
	print(("\033[93m" + "=========================================================="))
	print(("== Signing %s  using %s  id %s " % (binfile, key, idNum)))
	print(("==========================================================" + "\x1b[0m"))

	Sign_binary_openssl_or_HSM(binfile, begin_offset, key, embed_signature, outputFile, TypeOfKey, pinCode,idNum ,isECC, isLMS , lms_key)
	

if __name__ == "__main__":
	args = sys.argv
	# args[0] = current file
	# args[1] = function name
	# args[2:] = function args : (*unpacked)
	globals()[args[1]]( * args[2: ])
	
	
