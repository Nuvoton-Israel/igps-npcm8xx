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
				if '-' in offset_hex:
					print_dbg(offset_hex)
					offset_hex = offset_hex.split('-')[0].strip()
				elif ',' in offset_hex:
					print_dbg(offset_hex)
					offset_hex = offset_hex.split(',')[0].strip()
				
				offset = int(offset_hex, 16)
				size = int(register.get('size'),16)
				
				# sometimes there are errors in size, round it up:
				size = min([8, 16, 32], key=lambda x: abs(x - size))
				
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
					'size': size,
					'fields': fields
				})
				
				

		# Print the list of registers
		for register in registers:
			print_dbg(f"Register Name: {register['module'].get('name')} : {register['name']}, Offset: {register['offset']}, Size: {register['size']}")
			#for field in register['fields']:
			#	print(f"    Field Name: {field['name']}, Bitwise Mask: 0x{field['bitwise_mask']:X}")
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
					if ((len(row) == 6) or (len(row) == 5)):
						stripped_row = [field.strip() for field in row]
						module, register_name, field_name, value_hex, reset_hex, *delay = stripped_row
						delay = delay[0] if delay else 0
						value = hex_to_int(value_hex)
						reset = hex_to_int(reset_hex)
						module_index = int(module)

						print_dbg("\n")
						
						print_dbg(row)
						
						result = [register for register in registers if register_name == register['name']]
						print_dbg(result)
						if not result:
							print_dbg ("Reg " + register_name + " not found in chip file")
							continue
						reg = result[0]
						reg_name = reg.get('name')
						print_dbg(reg_name)
						Size = reg['size']
						bit_offset_num = 0

						mask = 0
						if (field_name == '0'):
							mask = 0xFFFFFFFF
						else:
							for f in reg.get("fields"):
								if (field_name == f.get("name")):
									mask = f.get("bitwise_mask")
									bit_offset_num = f.get("bit_offset")
						
						module_element = reg.get("module")
						value = value << bit_offset_num

						if module_element is not None:
							base_addresses_str = module_element.get("base_address")
							multiple = module_element.get("multiple")
							multiple_name_index = int(module_element.get("multiple_name_index", 1))
							module_name_pattern = module_element.get("multiple_name_pattern", "[NAME][INDEX]")
							
							print_dbg(f"Module: {reg['module'].get('name')} reg: {reg['name']}, addr: {hex(int(reg['offset']))}, Size: {reg['size']}")

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
								print("{0:#0{1}x}".format((addr[module_index] + int(reg.get('offset'))),10) , "{0:#0{1}x}".format(mask, 10), "{0:#0{1}x}".format(value, 10), "{0:#0{1}x}".format(reset, 5), delay, Size)
								
								# pack the values in a packed binary for the TIP_FW to parse:
								binary_data = struct.pack('<IIIBBH', addr[module_index] + int(reg.get('offset')), int(value), int(mask), int(Size)>>4, int(delay), int(reset))

								binary_file.write(binary_data)
							else:
								print(f"base '{register_name}' is missing base_address or multiple attribute. Skipping row.")

					else:
						print("Invalid row format. Each row should contain register_name, value, and reset.")
			
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

