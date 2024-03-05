# SPDX-License-Identifier: GPL-2.0
#
# Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
#
# Copyright (C) 2023 Nuvoton Technologies, All Rights Reserved
#-------------------------------------------------------------------------

import sys
import os
import time
import struct
import csv
import re
import math

from shutil import copy
from shutil import move
from shutil import rmtree
import xml.etree.ElementTree as ET
from pathlib import Path

from .BinarySignatureGenerator import *
from .GenerateKeyECC import *
from .GenerateKeyRSA import *
from .BinaryGenerator import *
from .CRC32_Generator import *
from .IGPS_files import *


# set to 1 to print more info, 0 othersize
debug_mode = 0


def print_dbg(str):
	if(debug_mode == 1):
		print(str)


# Use this script to combine Chip XML files to a single files.
# this is needed for IGPS developers only, since we get the XML split per module
def xml_com():

	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	
	print(currpath)
	
	# Path to the directory containing your XML files
	xml_directory = Path(os.path.join(currpath,"ImageGeneration",  "versions", "chip"))
	# Path("P:\Projects\Arbel\work\tali\WS\IGPSs\BMC_Programming_Scripts_DEV_1\deliverables\IGPS_3.9.8_Internal\py_scripts\ImageGeneration\versions\chip")

	# Output XML file
	output_xml_path = os.path.join(currpath,"ImageGeneration",  "versions", "chip", "ARBEL2.chip")

	# Create a new root element for the merged XML
	merged_root = ET.Element("MergedRoot")
	
	print(xml_directory)

	# Iterate over each XML file in the directory
	for xml_file_path in xml_directory.glob("*.chip"):
		print(xml_file_path)
		try:
			# Parse the XML file
			tree = ET.parse(xml_file_path)
			root = tree.getroot()

			# Iterate over each child element in the root and append it to the merged root
			for child_element in root:
				merged_root.append(child_element)

		except ET.ParseError as e:
			print(f"Error parsing {xml_file_path}: {e}")

		# Create a new tree with the merged root
		merged_tree = ET.ElementTree(merged_root)

		# Write the merged XML to a new file
		merged_tree.write(output_xml_path, encoding="utf-8", xml_declaration=True)

		print(f"Merged {xml_file_path} file written to {output_xml_path}")




# Function to convert hexadecimal string to integer
def hex_to_int(hex_str):
	return int(hex_str, 16)


# Future optional enhancement: parse register where the index is part of the name

# def get_register_index_range(reg_name_str, offset):
# 
# 	try:
# 		# Define a regular expression pattern to match any digit sequence or digit range separated by underscore
# 		pattern = r'([^\d_]+)(\d+)(?:_(\d+))?$'
# 
# 		# Reverse the string and use re.search() to find the first match from the end
# 		match = re.search(pattern, reg_name_str)
# 		
# 		if match:
# 			# Extract the start and end of the range (if available)
# 			print("get_register_index_range a")
# 
# 			num_groups = len(match.groups())
# 
# 			end = (match.group(num_groups)) if match.group(num_groups) else 0
# 			start = (match.group(num_groups-1)) if match.group(num_groups-1) else 0
# 
# 			# Extract the prefix string
# 			prefix = reg_name_str[0:(len(reg_name_str)- len(str(start)) - len(str(end)) -1)]
# 			
# 			# Generate an array of strings based on the range
# 			return [prefix, int(start), int(end)]
# 			
# 			
# 		pattern = r'([0-9A-Z_]+)(\d+)(?:_(\d+))?'
# 		
# 		# Use re.search() to find the first match in the string
# 		match = re.search(pattern, reg_name_str)
# 		
# 		# Handle straing like GPTIMER0LD0_1  (when there is a number in the middle of the name):
# 		if match:
# 			print("get_register_index_range b")
# 			groups = match.groups()
# 			# Convert the numeric groups to integers
# 			
# 			if (len(groups) >= 2):
# 				result = [groups[0]] + [int(num) for num in groups[1:] if num is not None]
# 				print(result)
# 				return result
# 
# 		# Handle straings like MCR_n
# 		if 'n' in reg_name_str:
# 			print("get_register_index_range c")
# 			print("string with n")
# 			
# 			replaced_string = reg_name_str.replace('n', '')
# 
# 			# Find the indices of 'n' 
# 			n_location = [i for i, char in enumerate(reg_name_str) if char == 'n']
# 			
# 			if (n_location != (len(reg_name_str) - 1)):
# 				prefix = reg_name_str[0:n_location] + reg_name_str[n_location+1:]
# 			return[prefix, 0, len(offset)-1]
# 			
# 			
# 			# Use re.search() to find the first match in the string
# 			# match = re.search(pattern, reg_name_str)
# 		
# 		return [reg_name_str, 0, 1]
# 		
# 	except (Exception) as e:
# 		exc_type, exc_obj, exc_tb = sys.exc_info()
# 		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
# 		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
# 		print("\n py_scripts\\ImageGeneration\\Register_csv_parse.py: get_register_index_range (%s)" % str(e))
# 		raise




def Register_file_chip_xml_parse(chip_xml):
	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	

	try:
		print (currpath, '\n')
		tree = ET.parse(chip_xml)
		root = tree.getroot()
		
		print(f"Parse '{chip_xml}' registers file of NPCM8XX")

		# Accessing elements and attributes
		for reg in root.findall('REGISTER'):
			name = reg.find('name').text
			offset = reg.find('offset').text
			size = reg.find('size').text
			print_dbg(f"Name: {name}, Offset: {offset}, Size: {size}")

		# List to store register information
		registers = []

		# Iterate over MODULE_CORE_MEM elements
		for module in root.findall('.//MODULE_CORE_MEM'):
		
		
			# Iterate over REGISTER elements within each MODULE_CORE_MEM
			for register in module.findall('.//REGISTER'):
				# Extract information from the REGISTER element
				register_name = register.get('name')
				offset_hex = register.get('offset')
				size = int(register.get('size'),16)
				# sometimes there are errors in size, round it up:
				size = min([8, 16, 32], key=lambda x: abs(x - size))
				size_byte_count = int(size) / 8
				
				# create an array of one or more offsets per register:
				offset_start = 0
				offset_end = 0
				offset = []
				# offset can be X-Y:
				if '-' in offset_hex:
					offset_start = int(offset_hex.split('-')[0].strip(), 16)
					offset_end = int(offset_hex.split('-')[1].strip(), 16)
					for ind in range(int((offset_end - offset_start)/(size_byte_count))):
						offset.append(int(offset_start + (size_byte_count) * ind))
				
				# offset can be comma seperated:
				elif ',' in offset_hex:
					offset_array = offset_hex.split(',')
					for ind in range(len(offset_array)):
						offset.append(int(offset_array[ind].strip(), 16))
				else:
					offset.append(int(offset_hex, 16))
				
				# cehck if register has multiple property in the XML:
				reg_multiple = register.get('multiple') 
				if reg_multiple is None:
					reg_multiple = 1
				else:
					reg_multiple = int(reg_multiple)


				if isinstance(offset, int):
					len_offset = 1
				elif isinstance(offset, list):
					len_offset =  len(offset)
				else:
					len_offset =  0

				if len_offset != reg_multiple :
					print("size mismatch error in reg " + register_name + " multiple " + str(reg_multiple) + " offsets " + str(len_offset))
					len_offset = max(len_offset, reg_multiple)
					reg_multiple = len_offset
					
				# optional: parse string nicely:
				#  if len_offset > 1:
				#  	print(get_register_index_range(register_name, offset)) 	
				
				# Extract fields from the REGISTER element
				fields = []
				for field in register.findall('.//FIELD'):
					field_name = field.get('name')
					bit_offset_val = int(field.get('bit_offset'))
					bit_size = int(field.get('bit_size'))
					bitwise_mask = ((1 << bit_size) - 1) << bit_offset_val
					fields.append({
						'name': field_name,
						'bitwise_mask': bitwise_mask,
						'bit_offset': bit_offset_val
					})

				# Append the information to the registers list
				registers.append({
						'module': module,
						'name': register_name,
						'offset': offset,
						'size': math.log2(int(size_byte_count)),
						'fields': fields,
						'Multi' : reg_multiple
					})


		# Print the list of registers
		for register in registers:
			print_dbg(f"Register Name: {register['module'].get('name')} : {register['name']}, Offset: {register['offset']}, Size: {register['size']}")
			#for field in register['fields']:
			#	print(f"	Field Name: {field['name']}, Bitwise Mask: 0x{field['bitwise_mask']:X}")
		return registers
		
	except (Exception) as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print("\n py_scripts\\ImageGeneration\\Register_csv_parse.py: Register_file_chip_xml_parse (%s)" % str(e))
		raise

	finally:
		os.chdir(currpath)

##############################################################################################################################
				

def Register_csv_file_handler(input_file_path, output_file_path, registers):
	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	

	try:
		print ("\n", currpath)
		
		if (os.path.isfile(input_file_path) == False):
			print ("File " , input_file_path, " not found\n")
			return

		print(f"Parse '{input_file_path}' to create binary file '{output_file_path}' for TIP")
		
		print("-------------------------------------------------")
		print("addr       mask       value      reset delay size")
		print("-------------------------------------------------")
		# parse input  file and create output binary:
		with open(input_file_path, 'r') as csv_file:
			csv_reader = csv.reader(csv_file)
			
			# Open binary file for writing
			with open(output_file_path, 'wb') as binary_file:
				# Iterate through each line in the CSV file
				for row in csv_reader:
					# Skip lines starting with '#' (considered as comments)
					if row and row[0].startswith('#'):
						continue
					if ((len(row) == 6) or (len(row) == 7)):
						stripped_row = [field.strip() for field in row]
						register_name, module, index, field_name, value_hex, reset_hex, *delay = stripped_row
						delay = delay[0] if delay else 0
						value = hex_to_int(value_hex)
						reset = hex_to_int(reset_hex)
						module_index = int(module)
						reg_index = int(index)
						result = [register for register in registers if register_name == register['name']]
						print_dbg(result)
						if not result:
							print ("Reg " + register_name + " not found in chip file")
							continue
						reg = result[0]
						reg_name = reg.get('name')
						print_dbg(reg_name)
						Size = int(reg['size'])
						bit_offset_num = 0

						mask = 0
						field_found = 0
						if (field_name == '0'):
							mask = 0xFFFFFFFF
							field_found = 1
						else:
							for f in reg.get("fields"):
								if (field_name == f.get("name")):
									field_found = 1
									mask = f.get("bitwise_mask")
									bit_offset_num = f.get("bit_offset")
							if (field_found == 0):
								# blind search of field in other registers
								for register in registers:
									for f in register.get("fields"):
										if (field_name == f.get("name")):
											print ("Found field ", field_name ," in other register ", f.get("name"))
											field_found = 1
											mask = f.get("bitwise_mask")
											bit_offset_num = f.get("bit_offset")

						if (field_found == 0):
							print("Field ", field_name, " in register ", register_name, " not found")
							continue
						module_element = reg.get("module")
						value = value << bit_offset_num

						if module_element is not None:
							base_addresses_str = module_element.get("base_address")
							multiple = module_element.get("multiple")
							multiple_name_index = int(module_element.get("multiple_name_index", 1))
							module_name_pattern = module_element.get("multiple_name_pattern", "[NAME][INDEX]")
							
							#print_dbg(f"Module: {reg['module'].get('name')} reg: {reg['name']}, addr: {hex(int(reg['offset'][reg_index]))}, Size: {reg['size']}")

							if base_addresses_str  is not None:
								addr = []
								if multiple:
									# Generate addresses based on multiple base addresses and attributes
									addresses = base_addresses_str.split(",")
									for cnt in range(len(addresses)):
										addr.append(hex_to_int(addresses[cnt]))
								else:
									addr.append(hex_to_int(base_addresses_str))
								
								# Iterate over generated addresses and write binary data
								offsets_array = reg.get('offset')
								if type(offsets_array) == list:
									if reg_index < len(offsets_array):
										offset_val = offsets_array[reg_index]
								else:
									offset_val = offsets_array

								print("{0:#0{1}x}".format(addr[module_index] + offset_val, 10) , "{0:#0{1}x}".format(mask, 10), "{0:#0{1}x}".format(value, 10), 
									"{0:#0{1}x}".format(reset, 5), delay, Size, stripped_row)
								
								# pack the values in a packed binary for the TIP_FW to parse:
								binary_data = struct.pack('<IIIBBH', addr[module_index] + offset_val, int(value), int(mask), int(Size), int(delay), int(reset))

								binary_file.write(binary_data)
							else:
								print(f"base '{register_name}' is missing base_address or multiple attribute. Skipping row.")

					else:
						print("Invalid row format.", row)
			
				# Get the current position within the file
				current_position = binary_file.tell()

				# Check if no data has been written
				if current_position == 0:
					print("No data was written.")
					binary_file.close()
					os.remove(output_file_path)
				else:
					print(f"{current_position} bytes were written.")
					print(f"Binary file '{output_file_path}' has been created.")

	except (Exception) as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print("Error at: " , fname, "line: ", exc_tb.tb_lineno)
		print("\n py_scripts\\ImageGeneration\\Register_csv_parse.py: Register_csv_file_handler (%s)" % str(e))
		raise

	finally:
		os.chdir(currpath)

