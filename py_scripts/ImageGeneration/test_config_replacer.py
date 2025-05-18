import unittest
import os
import json
import xml.etree.ElementTree as ET
from config_replacer import load_settings, replace_value_in_xml, replace_value_in_py
from config_replacer import replace_settings_in_json


class ConfigReplacerTestCase(unittest.TestCase):
    def setUp(self):
        self.settings_file = "test_settings.json"
        self.xml_file = "test.xml"
        self.py_file = "test.py"
        self.target_xml_file = "target_test.xml"
        self.target_py_file = "target_test.py"
        self.target_json_file = "target_test.json"

    def tearDown(self):
        if os.path.exists(self.settings_file):
            os.remove(self.settings_file)
        if os.path.exists(self.xml_file):
            os.remove(self.xml_file)
        if os.path.exists(self.py_file):
            os.remove(self.py_file)
        if os.path.exists(self.target_xml_file):
            os.remove(self.target_xml_file)
        if os.path.exists(self.target_py_file):
            os.remove(self.target_py_file)

    def test_load_settings(self):
        # Create a test settings file
        settings = {
            "//": "this is a comment",
            "BootBlockAndHeader.xml": {
                "//": "this is a comment",
                "MC_CONFIG": "0x05"
            },
            "key_setting_edit_me.py":
            {
                "comment": "this is a comment",
            },
            "key.json":
            {
                "COMBO1_OFFSET": "2048 * 1024",
                "data": 1234,
                "isECC": False,
                "lms_flags": {
                    "is_LMS_kmt": True,
                    "is_LMS_tip_fw_L0": False
                },
                "key": {"subkey": ["subvalue"]}
            }
        }
        settings_without_comment = {
            "BootBlockAndHeader.xml": {
                "MC_CONFIG": "0x05"
            },
            "key.json":
            {
                "COMBO1_OFFSET": "2048 * 1024",
                "data": 1234,
                "isECC": False,
                "lms_flags": {
                    "is_LMS_kmt": True,
                    "is_LMS_tip_fw_L0": False
                },
                "key": {"subkey": ["subvalue"]}
            }
        }
        with open(self.settings_file, "w") as f:
            json.dump(settings, f)

        # Test loading the settings file
        loaded_settings = load_settings(self.settings_file)
        self.assertEqual(loaded_settings, settings_without_comment)
        # test invalid file
        self.assertRaises(FileNotFoundError, load_settings,
                          "invalid_file.json")
        # test empty file
        with open(self.settings_file, "w") as f:
            f.write("")
        self.assertEqual(load_settings(self.settings_file), {})
        # test empty settings
        with open(self.settings_file, "w") as f:
            f.write("{}")
        self.assertEqual(load_settings(self.settings_file), {})
        # test invalid format
        with open(self.settings_file, "w") as f:
            f.write("invalid")
        self.assertRaises(json.JSONDecodeError,
                          load_settings, self.settings_file)

    def test_replace_value_in_xml(self):
        # Create a test XML file
        root = ET.Element("Root")
        element = ET.SubElement(root, "BinField")
        name = ET.SubElement(element, "name")
        name.text = "MC_CONFIG"
        content = ET.SubElement(element, "content")
        content.text = "0x01"
        e2 = ET.SubElement(root, "BinField")
        name2 = ET.SubElement(e2, "name")
        name2.text = "HOST_IF"
        content2 = ET.SubElement(e2, "content")
        content2.text = "0x01"
        tree = ET.ElementTree(root)
        tree.write(self.xml_file)

        # Define the replacement dictionary
        replacements = {
            "MC_CONFIG": "0x05",
        }
        not_exist_replacement = {
            "MC_CONFIG1": "0x05"
        }

        # Test replacing values in the XML file
        replace_value_in_xml(self.xml_file, replacements, self.target_xml_file)

        # Verify the replaced values, and other value should not be changed
        target_tree = ET.parse(self.target_xml_file)
        target_root = target_tree.getroot()
        target_elements = target_root.findall("BinField")
        target_element = target_elements[0]
        target_content = target_element.find("content")
        self.assertEqual(target_content.text, "0x05")
        target_content = target_element.find("name")
        self.assertEqual(target_content.text, "MC_CONFIG")
        target_element = target_elements[1]
        target_content = target_element.find("content")
        self.assertEqual(target_content.text, "0x01")
        target_content = target_element.find("name")
        self.assertEqual(target_content.text, "HOST_IF")
        self.assertRaises(ValueError, replace_value_in_xml, self.xml_file,
                          not_exist_replacement, self.target_xml_file)

    def test_replace_value_in_py(self):
        # Create a test Python file
        content = """
        Aaa = "0x01"
        Bbb = "0x02"
        Ccc = 123
        """
        with open(self.py_file, "w") as f:
            f.write(content)

        # Define the replacement dictionary
        replacements = {
            "Aaa": "\"0x05\""
        }
        # Error case
        not_exist_replacement = {
            "Ddd": "0x05"
        }
        case_replacement = {
            "CCC": "0x05"
        }

        # Test replacing values in the Python file
        replace_value_in_py(self.py_file, replacements, self.target_py_file)

        # Verify the replaced values
        with open(self.target_py_file, "r") as f:
            target_content = f.read()
        self.assertIn('Aaa = "0x05"', target_content)
        self.assertRaises(ValueError, replace_value_in_py, self.py_file,
                          not_exist_replacement, self.target_py_file)
        self.assertRaises(ValueError, replace_value_in_py, self.py_file,
                          case_replacement, self.target_py_file)
        self.assertIn('Ccc = 123', target_content)

    def test_replace_value_in_json(self):
        # Create a test json settings file
        content = {
            "otp_key_which_signs_kmt": "otp_key1",
            "kmt_key_which_signs_tip_fw_L0": "kmt_key0",
            "isECC": True,
            "lms_flags": {
                "is_LMS_kmt": False,
                "is_LMS_tip_fw_L0": False,
                "is_LMS_uboot": True
            },
            "key_groups": {
                "KMT_Keys": [
                    "is_LMS_tip_fw_L0",
                    "is_LMS_skmt"
                ],
                "SKMT_Keys": [
                    "is_LMS_tip_fw_L1",
                    "is_LMS_uboot"
                ]
            },
            "COMBO1_OFFSET": 524288
        }
        with open(self.settings_file, "w") as f:
            json.dump(content, f)
        # Define the replacement dictionary
        replacements = {
            "COMBO1_OFFSET": "2048 * 1024",
            "isECC": False,
            "lms_flags": {
                "is_LMS_kmt": True,
                "is_LMS_tip_fw_L0": False
            },
            "key_groups": {
                "KMT_Keys": [
                    "is_LMS_skmt"
                ],
                "SKMT_Keys": [
                    "is_LMS_tip_fw_L1",
                    "is_LMS_OpTee",
                    "is_LMS_uboot"
                ]
            }
        }
        not_exist_replacement = {
            "COMBO1_OFFSET0": 2048576
        }
        # Test replacing values in the JSON file
        replace_settings_in_json(self.settings_file, replacements,
                                 self.target_json_file)
        # Verify the replaced values
        with open(self.target_json_file, "r") as f:
            target_content = json.load(f)
        self.assertEqual(target_content["COMBO1_OFFSET"], 2097152)
        self.assertEqual(target_content["isECC"], False)
        self.assertEqual(target_content["lms_flags"]["is_LMS_kmt"], True)
        self.assertEqual(target_content["lms_flags"]
                         ["is_LMS_tip_fw_L0"], False)
        self.assertEqual(target_content["lms_flags"]["is_LMS_uboot"], True)
        self.assertEqual(target_content["key_groups"]["KMT_Keys"],
                         ["is_LMS_skmt"])
        self.assertEqual(target_content["key_groups"]["SKMT_Keys"],
                         ["is_LMS_tip_fw_L1", "is_LMS_OpTee", "is_LMS_uboot"])
        self.assertRaises(ValueError, replace_settings_in_json,
                          self.settings_file, not_exist_replacement,
                          self.target_json_file)


if __name__ == "__main__":
    unittest.main()
