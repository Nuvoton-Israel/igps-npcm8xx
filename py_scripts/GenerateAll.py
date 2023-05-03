# SPDX-License-Identifier: GPL-2.0
#
# Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
#
# Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
#-------------------------------------------------------------------------

import os
import sys
import ImageGeneration.GenerateImages
import ImageGeneration.GenerateImagesPartial


try:
	currpath = os.getcwd()
	os.chdir(os.path.dirname(os.path.abspath(__file__)))

	pinCode = "0"
	component_num = "0"
	runPartial = False
	isPalladium = False
	TypeOfKey = "openssl"


	index = 1
	while index < len(sys.argv):

		if (sys.argv[index] == "partial"):
			runPartial = True

		elif (sys.argv[index] == "palladium"):
			isPalladium = True
			
		elif (sys.argv[index] == "openssl"):
			TypeOfKey = "openssl"

		elif (sys.argv[index] == "RemoteHSM"):
			TypeOfKey = "RemoteHSM"
			print("No keys will be generated. Signing remotely in HSM")
		
		elif ((sys.argv[index] == "HSM") or (sys.argv[index] == "hsm")):
			TypeOfKey = "HSM"

		else:
			component_num = sys.argv[index]
		index += 1

	if TypeOfKey == "HSM":
		msg = "please enter user name pin: \n"
		reply1 = str(input(msg).strip())
		msg = "please enter user name pin again to verify: \n"
		reply2 = str(input(msg).strip())
		if reply1 == reply2:
			pinCode = reply1
		else:
			TypeOfKey = "openssl"
			print("not the same pin ! using open SSL instead ")
			

	# if (len(sys.argv) >= 4): #3rd param may be the flag "partial" \ "palladium", 4th param may be "palladium"
		#option 1) .\py_scripts\GenerateAll.py openssl\HSM  0 partial
		#option 2) .\py_scripts\GenerateAll.py openssl\HSM  0 palladium
		#option 3) .\py_scripts\GenerateAll.py openssl\HSM  0 partial palladium


	if (runPartial):
		print("==========================================================")
		print("== Replace Single Componenet of Images")
		print("==========================================================")
		ImageGeneration.GenerateImagesPartial.ReplaceComponent(TypeOfKey, pinCode, isPalladium, str(component_num)) 
	else:		
		print("==========================================================")
		print("== Generate All Images")
		print("==========================================================")
		ImageGeneration.GenerateImages.Run(TypeOfKey, pinCode, isPalladium)

except Exception as e:
	print("\n***************************************************")
	print("*******                                      ******")
	print("*******   ########     #      ###   #        ******")
	print("*******   #           # #      #    #        ******")
	print("*******   #          #   #     #    #        ******")
	print("*******   ########  #######    #    #        ******")
	print("*******   #         #     #    #    #        ******")
	print("*******   #         #     #    #    #        ******")
	print("*******   #         #     #   ###   #######  ******")
	print("*******                                      ******")
	print("***************************************************")
	print(e)
	pass
finally:
	os.chdir(currpath)
