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

class GenerateKeyRSAError(Exception):
	def __init__(self, value):
		self.strerror = "Generate RSA Key error value:" + str(value)
	def __str__(self):
		return repr(self.strerror)

def executeCMD(cmd):
	print(cmd)
	rc = os.system(cmd)
	if rc != 0:
		print("execute CMD failed \n")
		

		   
def GenerateKeyRSA(keyFileName, TypeOfKey, pinCode, idNum):

	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	splited = keyFileName.split(mark)
	keysFolder = "keys" + mark +  TypeOfKey
	newFileName = keysFolder + mark + splited[-1]
	

	prv_key_pem = newFileName.replace(".der", ".pem")
	pub_key_der = newFileName.replace(".", "_pub.", 1)
	pub_key_pem = newFileName.replace(".der", ".pem")
	
	if os.path.isdir(keysFolder) == False:
		print(("create folder: " + keysFolder))
		os.mkdir(keysFolder)
	
	if TypeOfKey == "openssl":
		GenerateKeyRSA_OpenSSL(newFileName)
	else:   #assuming HSM, requires pinCode
		GenerateKeyRSA_HSM(newFileName, pinCode, idNum)
	
	#in the end copy the keys from "keys" folder whether they were created now or before,
	# into the "inputs\key_inputs" folder (root's original location)
	# copy_tree(keysFolder, splited[0])
	
	CheckIfFileExistsAndMove(pub_key_der, input_key_dir)
	CheckIfFileExistsAndMove(pub_key_pem, input_key_dir)
	CheckIfFileExistsAndMove(prv_key_pem, input_key_dir)
	


def GenerateKeyRSA_OpenSSL(keyFileName):
	try:
		_openssl = openssl
		if os.name != "nt":
			_openssl = linux_prefix + openssl

		currpath = os.getcwd()
		os.chdir(os.path.dirname(os.path.abspath(__file__)))
		
		print("===============================================================")
		print(("==Generate RSA 2048 Key pair and save to file " + keyFileName + "     ="))
		print("================================================================")
		

		prv_key_pem = keyFileName.replace(".der", ".pem")

		pub_key_der = keyFileName.replace(".", "_pub.", 1)
		pub_key_pem = pub_key_der.replace(".der", ".pem")


		if (os.path.isfile(pub_key_der) == True):
			print(("File " + str(pub_key_der) + " exists. Avoid override"))
			return
			
			
		# openssl req -new -x509 -sha256 -newkey rsa:2048 -nodes -keyout private.pem -days 365 -out cert.pem
		# openssl rsa -in private.pem -pubout > public.pub



		# call openssl to generate an RSA key:   openssl genrsa -des3 -out private.pem 2048
		cmd = "%s  genrsa 2048 > %s " \
			  % (_openssl, prv_key_pem)
		executeCMD(cmd)

		# extract the public key and save to a separate file:
		# openssl rsa -in private.pem -outform PEM -pubout -out public.pem
		cmd = "%s  rsa  -outform pem  -inform pem -in \"%s\" -pubout -out \"%s\"" \
			  % (_openssl, prv_key_pem, pub_key_pem)
		executeCMD(cmd)

		cmd = "%s  rsa  -outform der  -inform pem -pubout -in \"%s\" > \"%s\"" \
			  % (_openssl, prv_key_pem, pub_key_der)
		executeCMD(cmd)

	except:
		print(("Generate Key failed" % (keyFileName)))
		raise
	finally:
		os.chdir(currpath)

def GenerateKeyRSA_HSM(keyFileName, pinCode, idNum):

	splited = keyFileName.split(mark)
	label = splited[-1]
	try:
		print("==================================================================")
		print(("==Generate RSA384 HSM Key pair and save to file " + keyFileName + "     ="))
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
		cmd = "pkcs11-tool.exe -l --keypairgen --pin " + pinCode + "  --key-type RSA:2048 --id " + idNum + " --label " + label
		executeCMD(cmd)

		#create DER file from public
		print(("public keyFileName is: " + keyFilePub))
		cmd = "pkcs11-tool.exe --read-object --type pubkey --id " + idNum+" -o " + keyFilePub
		executeCMD(cmd)



	except:
		print(("Generate Key HSM failed" % (keyFilePub)))
		raise

	finally:
		os.chdir(currpath)




