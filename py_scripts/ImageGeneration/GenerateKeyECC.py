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
from .BinarySignatureGenerator import *
from .IGPS_files import *



linux_prefix = " ./"
openssl = "openssl"
mark = "\\"
linux_Mark = "/"
if os.name != "nt":
	mark = linux_Mark

class GenerateKeyECCError(Exception):
	def __init__(self, value):
		self.strerror = "Generate ECC Key error value:" + str(value)
	def __str__(self):
		return repr(self.strerror)

def executeCMD(cmd):
	print(cmd)
	rc = os.system(cmd)
	if rc != 0:
		print("execute CMD failed \n")
		   
def GenerateKeyECC(keyFileName, TypeOfKey, pinCode, idNum):

	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	splited = keyFileName.split(mark)
	keysFolder = "keys" + mark +  TypeOfKey
	newFileName = keysFolder + mark + splited[-1]


	pub_key_der = newFileName.replace(".", "_pub.", 1)
	pub_key_bin = newFileName.replace(".der", "_pub.bin", 1)
	
	if os.path.isdir(keysFolder) == False:
		print(("create folder: " + keysFolder))
		os.mkdir(keysFolder)
	
	if TypeOfKey == "openssl":
		GenerateKeyECC_OpenSSL(newFileName)
	else:   #assuming HSM, requires pinCode
		GenerateKeyECC_HSM(newFileName, pinCode, idNum)
	
	#in the end copy the keys from "keys" folder whether they were created now or before,
	# into the "inputs\key_inputs" folder (root's original location)
	# copy_tree(keysFolder, splited[0])
	
	CheckIfFileExistsAndMove(newFileName, input_key_dir)
	CheckIfFileExistsAndMove(pub_key_der, input_key_dir)
	CheckIfFileExistsAndMove(pub_key_bin, input_key_dir)


def GenerateKeyECC_OpenSSL(keyFileName):
	try:
		_openssl = openssl
		if os.name != "nt":
			_openssl = linux_prefix + openssl

		currpath = os.getcwd()
		os.chdir(os.path.dirname(os.path.abspath(__file__)))
		
		print("===============================================================")
		print(("==Generate ECC384 Key pair and save to file " + keyFileName + "     ="))
		print("================================================================")
		pub_key_der = keyFileName.replace(".", "_pub.", 1)
		pub_key_pem = pub_key_der.replace(".der", "_key.pem")


		if (os.path.isfile(pub_key_der) == True):
			print(("File " + str(pub_key_der) + " exists. Avoid override"))
			return


			# call openssl to generate a key
		cmd = "%s  ecparam -name secp384r1 -genkey -noout -out \"%s\" -outform der" \
			  % (_openssl, keyFileName)
		executeCMD(cmd)

		# extract the public key and save to a separate file:
		# openssl ec -in secp384r1-key1.pem -pubout > secp384r1-key1_pub.pem
		cmd = "%s  ec  -outform pem  -inform der -in \"%s\" -pubout > \"%s\"" \
			  % (_openssl, keyFileName, pub_key_pem)
		executeCMD(cmd)

		cmd = "%s  ec  -outform der  -inform der -in \"%s\" -pubout > \"%s\"" \
			  % (_openssl, keyFileName, pub_key_der)
		executeCMD(cmd)

		# convert the key to binary (to be used by inputs\arbel_fuse_map.xml)
		output_bin_file = keyFileName.replace(".der", "_pub.bin")
		Extract_bin_public_key_from_DER_file(keyFileName, output_bin_file)
		
		os.remove(pub_key_pem)
		
	except:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print(("Generate Key failed" % (keyFileName)))
		raise
	finally:
		os.chdir(currpath)

def GenerateKeyECC_HSM(keyFileName, pinCode, idNum):

	splited = keyFileName.split(mark)
	label = splited[-1]
	try:
		print("==================================================================")
		print(("==Generate ECC384 HSM Key pair and save to file " + keyFileName + "     ="))
		print("==================================================================")
		
		keyFilePub = keyFileName.replace(".der", "_pub.der")
		currpath = os.getcwd()
		os.chdir(os.path.dirname(os.path.abspath(__file__)))
		print(("search for: " + keyFilePub))
		if (os.path.isfile(keyFilePub) == True):
			print(("File " + str(keyFilePub) + " exists. Avoid override"))
			return

		#delete the key if exists - dont remove this from comment unless necessay ! use "DeleteAllNitroKeys.py"
		#cmd ="pkcs11-tool.exe -l --pin "+pinCode+" --delete-object --type privkey --id "+idNum
		#executeCMD(cmd)

		#create the key
		cmd = "pkcs11-tool.exe -l --keypairgen --pin " + pinCode + "  --key-type EC:secp384r1 --id " + idNum + " --label " + label
		executeCMD(cmd)

		#create DER file from public
		print(("public keyFileName is: " + keyFilePub))
		cmd = "pkcs11-tool.exe --read-object --type pubkey --id " + idNum+" -o " + keyFilePub
		executeCMD(cmd)

		output_bin_file = keyFilePub.replace(".der", ".bin")
		Extract_bin_public_key_from_DER_file(keyFilePub, output_bin_file, 0) #0 means no private key on DER file

	except:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print(("Generate Key HSM failed" % (keyFilePub)))
		raise

	finally:
		os.chdir(currpath)




