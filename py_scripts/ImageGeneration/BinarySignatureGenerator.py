# SPDX-License-Identifier: GPL-2.0
#
# Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
#
# Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
#-------------------------------------------------------------------------

import sys
import os

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
	print(cmd)
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

def Sign_binary_openssl_or_HSM(bin_filename, begin_offset, key, embed_signature, output_filename , TypeOfKey, pinCode, idNum):
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
		# write the input with the embedded signature to the output file
		print(("write to output file " + output_filename))
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



def Embed_external_sig(sig_der, input_file, output_file, embed_signature):
	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	
	print(("\033[95m" + "=========================================================="))
	print(("== Embed external sig %s  to %s    " % (sig_der, input_file)))
	print(("==========================================================" + "\x1b[0m"))

	try:
		# read input file:
		if (os.path.isfile(input_file) == False):
			print(("\033[91m" + "Embed_external_sig: input file " + input_file + " is missing\n\n" + "\033[97m"))
			raise Exception('Missing file')
		
		if (os.path.isfile(sig_der) == False):
			print(("\033[91m" + "Embed_external_sig: sig file " + sig_der + " is missing\n\n" + "\033[97m"))
			raise Exception('Missing file')
		
		bin_file = open(input_file, "rb")
		input = bin_file.read()
		bin_file.close()

		# get the generated signature and embed it in the input binary
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
		
		# write the input with the embedded signature to the output file
		print(("write to output file " + output_file))
		output_file = open(output_file, "w+b")
		output_file.write(output)
		output_file.close()
	except:
		print(("\n\n Embed_external_sig.py: embed external key %s to %s failed" % (input_file, output_file)))
		raise Exception('Embed_external_sig')
	finally:
		os.chdir(currpath)

	os.chdir(currpath)
	
# Replace_binary_single_byte: used to embed the key index inside the image. usually at offset 0x140.
def Replace_binary_single_byte(binfile, offset, value):
	print(("**** Insert %s offset %s value %s ****" % (binfile, str(offset), str(value))))

	if (os.path.isfile(binfile) == False):
		print(("currpath " +  os.getcwd()))
		print(("\033[91m" + "Replace_binary_single_byte   Error: " +  binfile + " file is missing\n\n" + "\033[97m"))
		return -1
		
	with open(binfile, 'rb+') as f:
		f.seek(int(offset))
		f.write((chr(int(value))).encode('utf8'))
	
	f.close()


# Replace_binary_array: used to embed an array inside an image. Used for timestamp and address pointers.
# bArray=True: num is an array, just write it in the file
# bArray=False: num is a number in little endian, convert to array
def Replace_binary_array(input_file, offset, num, size, bArray, title):
	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	
	print(("\033[95m" + "=========================================================="))
	print(("== %s Replace_binary_array file %s offset %s num %s    " % (title, input_file, str(offset), str(num))))
	print(("==========================================================" + "\x1b[0m"))

	try:
		# read input file:
		if (os.path.isfile(input_file) == False):
			print(("\033[91m" + "Replace_binary_array: input file " + input_file + " is missing\n\n" + "\033[97m"))
			raise Exception('Missing file')

		bin_file = open(input_file, "rb")
		input = bin_file.read()
		bin_file.close()

		if (bArray == True):
			arr = BigNum_2_Array(num, size, True)
		else:
			arr = bytearray(num)

		#print(("size of input " + str(len(input))))
		output = input[:offset] + arr + input[(offset + size):]
		
		# write the input with the embedded signature to the output file
		print(("write " + str(arr) + " to file " + input_file))
		input_file = open(input_file, "w+b")
		input_file.write(output)
		input_file.close()
	except:
		print(("\n\n FAIL %s Replace_binary_array.py: file %s offset %s array %s    " % (title, input_file, str(offset), str(arr))))
		raise Exception('Replace_binary_array')
	finally:
		os.chdir(currpath)

	os.chdir(currpath)

	
def Sign_binary(binfile, begin_offset, key, embed_signature, outputFile, TypeOfKey, pinCode , idNum):

	
	print(("\033[93m" + "=========================================================="))
	print(("== Signing %s  using %s  id %s " % (binfile, key, idNum)))
	print(("==========================================================" + "\x1b[0m"))

	Sign_binary_openssl_or_HSM(binfile, begin_offset, key, embed_signature, outputFile, TypeOfKey, pinCode,idNum)
	

if __name__ == "__main__":
	args = sys.argv
	# args[0] = current file
	# args[1] = function name
	# args[2:] = function args : (*unpacked)
	globals()[args[1]]( * args[2: ])
	
	
