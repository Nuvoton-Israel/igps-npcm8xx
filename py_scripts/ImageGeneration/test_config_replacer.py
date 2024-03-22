import unittest
import os
import json
import xml.etree.ElementTree as ET
from config_replacer import load_settings, replace_value_in_xml, replace_value_in_py

class ConfigReplacerTestCase(unittest.TestCase):
    def setUp(self):
        self.settings_file = "test_settings.json"
        self.xml_file = "test.xml"
        self.py_file = "test.py"
        self.target_xml_file = "target_test.xml"
        self.target_py_file = "target_test.py"

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
            "BootBlockAndHeader.xml": {
                "MC_CONFIG": "0x05"
            }
        }
        with open(self.settings_file, "w") as f:
            json.dump(settings, f)

        # Test loading the settings file
        loaded_settings = load_settings(self.settings_file)
        self.assertEqual(loaded_settings, settings)
        # test invalid file
        self.assertRaises(FileNotFoundError, load_settings, "invalid_file.json")
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
        self.assertRaises(json.JSONDecodeError, load_settings, self.settings_file)

    def test_replace_value_in_xml(self):
        # Create a test XML file
        root = ET.Element("Root")
        element = ET.SubElement(root, "BinField")
        name = ET.SubElement(element, "name")
        name.text = "MC_CONFIG"
        content = ET.SubElement(element, "content")
        content.text = "0x01"
        e2 = ET.SubElement(root, "BinField")
        name2 = ET.SubElement(element, "name")
        name2.text = "HOST_IF"
        content2 = ET.SubElement(element, "content")
        content2.text = "0x01"
        tree = ET.ElementTree(root)
        tree.write(self.xml_file)

        # Define the replacement dictionary
        replacements = {
            "MC_CONFIG": "0x05"
        }
        not_exist_replacement = {
            "MC_CONFIG1": "0x05"
        }

        # Test replacing values in the XML file
        replace_value_in_xml(self.xml_file, replacements, self.target_xml_file)

        # Verify the replaced values
        target_tree = ET.parse(self.target_xml_file)
        target_root = target_tree.getroot()
        target_element = target_root.find("BinField")
        target_content = target_element.find("content")
        self.assertEqual(target_content.text, "0x05")
        self.assertRaises(ValueError, replace_value_in_xml, self.xml_file, not_exist_replacement, self.target_xml_file)

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
        self.assertRaises(ValueError, replace_value_in_py, self.py_file, not_exist_replacement, self.target_py_file)
        self.assertRaises(ValueError, replace_value_in_py, self.py_file, case_replacement, self.target_py_file)
        self.assertIn('Ccc = 123', target_content)

if __name__ == "__main__":
    unittest.main()