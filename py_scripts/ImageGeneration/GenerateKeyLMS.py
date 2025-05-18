# SPDX-License-Identifier: GPL-2.0
#
# Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
#
# Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
#-------------------------------------------------------------------------
import sys
import os

import json
# Define the correct path to the JSON file
json_file_path = os.path.join(os.path.dirname(__file__), 'key_setting_edit_me.json')
# Load the JSON configuration
with open(json_file_path, 'r') as file:
	config = json.load(file)
# Use the configuration values

# Calculate isLMS based on lms_flags
lms_flags = config.get("lms_flags", {})
isLMS = any(lms_flags.values())

if isLMS:
	from hsslms import LMS_Priv
	from hsslms.utils import *
from shutil import move
from shutil import copyfile
from .BinarySignatureGenerator import *
from .IGPS_files import *
import pickle
import inspect

linux_prefix = " "
openssl = "openssl"
mark = "\\"
linux_Mark = "/"
if os.name != "nt":
	mark = linux_Mark

class GenerateKeyLMSError(Exception):
	def __init__(self, value):
		self.strerror = "Generate LMS Key error value:" + str(value)
	def __str__(self):
		return repr(self.strerror)

		   
def GenerateKeyLMS(keyFileName, TypeOfKey, pinCode, idNum):

	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	splited = keyFileName.split(mark)
	keysFolder = "keys" + mark +  TypeOfKey
	newFileName = keysFolder + mark + splited[-1]
	newFileName = newFileName.replace(".", "_pub.", 1)  
	pub_key_bin = newFileName.replace("pub", "pickled_pub", 1)
	priv_key_bin = newFileName.replace("pub", "pickled_priv", 1)
	
	if os.path.isdir(keysFolder) == False:
		print(("create folder: " + keysFolder))
		os.mkdir(keysFolder)
	
	if TypeOfKey == "openssl":
		GenerateKeyLMS_OpenSSL(newFileName)
	else:	#assuming HSM, requires pinCode
		GenerateKeyLMS_HSM(newFileName, pinCode, idNum)
	
	# in the end copy the keys from "keys" folder whether they were created now or before,
	# into the "inputs\key_inputs" folder (root's original location)
	
	# LMS keys take a long time to copy to inputs
	# so in case the keys already exists in the input_key_dir, don't force the copy.
	force_copy = False
	CheckIfFileExistsAndMove(newFileName, input_key_dir, force_copy)
	CheckIfFileExistsAndMove(priv_key_bin, input_key_dir, force_copy)
	CheckIfFileExistsAndMove(pub_key_bin, input_key_dir, force_copy)
	

def GenerateKeyLMS_OpenSSL(keyFileName):
	try:
		_openssl = openssl
		if os.name != "nt":
			_openssl = linux_prefix + openssl

		currpath = os.getcwd()
		os.chdir(os.path.dirname(os.path.abspath(__file__)))
		
		print("===============================================================")
		print(("==Generate LMS  Key pair and save to file " + keyFileName + "     ="))
		print("================================================================")
		
		output_bin_file = keyFileName
		public_pickled_bin_file = keyFileName.replace("_pub", "_pickled_pub")
		private_pickled_bin_file = keyFileName.replace("_pub", "_pickled_priv")
		if (os.path.isfile(private_pickled_bin_file) and os.path.isfile(public_pickled_bin_file) == True):
			print("File " + str(private_pickled_bin_file) +  " exists. Avoid override")
			return
		else:
			print("Creating a LMS private key that will be stored at: " + private_pickled_bin_file + ".....")
	
		# Note: for debug can change to H20 and W2 (validation test), or H20 w8
		priv_key = LMS_Priv(LMS_ALGORITHM_TYPE.LMS_SHA256_M32_H20, LMOTS_ALGORITHM_TYPE.LMOTS_SHA256_N32_W4)
		print("LMS PRIV key ready")
		pub_key = priv_key.gen_pub()
		
		write_buffer_to_file(pub_key.get_pubkey(), output_bin_file)
	
		# Serialize the updated private key + public key to file
		with open(private_pickled_bin_file, 'wb') as f:
			pickle.dump(priv_key, f)
		with open(public_pickled_bin_file, 'wb') as f:
			pickle.dump(pub_key, f)
		
	except:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print(("Generate Key failed" % (keyFileName)))
		raise
	finally:
		os.chdir(currpath)
		
def write_buffer_to_file(buffer, filename):
	try:
		with open(filename, "wb") as file:
			file.write(buffer)
	except Exception as e:
		print(f'{e}')
	
def GenerateKeyLMS_HSM(keyFileName, pinCode, idNum):
	print("GenerateKeyLMS_HSM to do")


