# SPDX-License-Identifier: GPL-2.0
#
# Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
#
# Copyright (C) 2022 Nuvoton Technologies, All Rights Reserved
#-------------------------------------------------------------------------

"""
Usage:
    python config_replacer.py settings.json
    Please note the working directory should be the root of the project.
    example:
        python py_scripts/ImageGeneration/config_replacer.py py_scripts/ImageGeneration/inputs/settings.json
Test:
    python py_scripts/ImageGeneration/test_config_replacer.py

This script is used for replacing the settings in the XML and Python files from Openbmc setting file.
It would be useful to reduce effort of maintaining full XML for each configuration.
"""

from itertools import chain

import configparser
import io
import json
import os
import sys
import xml.etree.ElementTree as ET

XML_PATH = os.path.join("py_scripts", "ImageGeneration", "inputs")
KEY_SETTINGS_PATH = os.path.join("py_scripts", "ImageGeneration")
SETTING_FILE = os.path.join(XML_PATH, "settings.json")


def load_settings(file: str = SETTING_FILE) -> dict[str, dict[str, str]]:
    """
    Loads the settings file and checks if the file exists and is not empty.

    Args:
        file (str): The settings file to load. Defaults to SETTING_FILE.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file format is invalid.

    Returns:
        dict[str, dict[str, str]]: The settings dictionary.

    Example of the settings file:
    {
        "BootBlockAndHeader.xml":
        {
            "MC_CONFIG": "0x05"
        }
    }
    """
    if os.path.isfile(file) == False:
        raise FileNotFoundError(f"Error: {file} doesn't exist")
    # we should accept empty settings file or {} as valid
    settings = {}
    with open(file) as f:
        data = f.read().strip()
        if len(data) > 0:
            settings = json.loads(data)
    # check settings format
    for config, values in settings.items():
        if not isinstance(values, dict):
            raise ValueError(f"Error: Invalid format in settings file for {config}")
        for key, value in values.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError(f"Error: Invalid format in settings file for {config}")
    print("Settings format is valid")
    return settings


def replace_value_in_xml(xml_file: str, dict: dict[str, str], target_xml: str = None):
    """
    Replaces the values in the specified XML file with the given dictionary.

    Args:
        xml_file (str): The path to the XML file.
        dict (dict[str, str]): The dictionary containing the tag-value pairs to replace.
        target_xml (str, optional): The path to the target XML file. If not provided, the original XML file will be overwritten.

    Raises:
        ValueError: If a tag is not found in the XML file.

    Example:
        replace_value_in_xml("input.xml", {"TAG1": "VALUE1", "TAG2": "VALUE2"}, "output.xml")
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    # we only interested in the BinField elements
    elements = root.findall("BinField")
    # replace all the value pairs we defined
    for tag, value in dict.items():
        # search all the elements
        search_count = 0
        for element in elements:
            e = element.find("name")
            if e is not None and e.text is not None and e.text == tag:
                c = element.find("content")
                if c is None:
                    raise ValueError(f"Error: {tag} has no content")
                print(f"replacing {tag} value {c.text} to {value}")
                c.text = value
                break
            else:
                search_count += 1
        if search_count == len(elements):
            raise ValueError(f"Error: {tag} not found in the xml file")
    # write the xml file
    if target_xml is not None:
        tree.write(target_xml)
    else:
        tree.write(xml_file)
        pass


class NoSectionConfigParser:
    """
    Hacks class for ConfigParser to avoid read/write section in the configuration file.
    """

    def __init__(self):
        self._cp = configparser.RawConfigParser()
        self._cp.optionxform = lambda option: option

    def read(self, file: str):
        with open(file) as lines:
            lines = chain(("[DEFAULT]",), lines)
            self._cp.read_file(lines)
            return self._cp.defaults()

    def write(self, file: str):
        data = io.StringIO()
        self._cp.write(data)
        with open(file, "w") as f:
            f.write(data.getvalue().removeprefix("[DEFAULT]\n"))

    def set(self, key: str, value: str):
        dict = self._cp["DEFAULT"]
        if key not in dict:
            raise ValueError(f"Error: {key} not found in the configuration file")
        print(f"replacing {key} value {dict[key]} to {value}")
        dict[key] = value


def replace_value_in_py(py_file: str, dict: dict[str, str], target_py: str = None):
    """
    Replaces the values in the specified Python file with the given dictionary.

    Args:
        py_file (str): The path to the Python file.
        dict (dict[str, str]): The dictionary containing the key-value pairs to replace.
        target_py (str, optional): The path to the target Python file. If not provided, the original Python file will be overwritten.

    Raises:
        ValueError: If a key is not found in the configuration file.

    Example:
        replace_value_in_py("script.py", {"KEY1": "VALUE1", "KEY2": "VALUE2"}, "output.py")
    """
    cp = NoSectionConfigParser()
    cp.read(py_file)
    for key, value in dict.items():
        cp.set(key, value)
    if target_py is not None:
        cp.write(target_py)
    else:
        cp.write(py_file)


def replace_settings_test(file: str):
    # test the function, save results to the test folder
    settings = load_settings(file=file)
    for config in settings.keys():
        if config.endswith(".xml"):
            replace_value_in_xml(
                os.path.join(XML_PATH, config),
                settings[config],
                os.path.join("test", config),
            )
        elif config.endswith(".py"):
            replace_value_in_py(
                os.path.join(KEY_SETTINGS_PATH, config),
                settings[config],
                os.path.join("test", config),
            )
        else:
            raise ValueError(f"Error: {config} is not a supported configuration")

def change_pwd_to_script_root() -> tuple[str, str]:
    # change the working directory to the root of the project
    root = "py_scripts"
    pwd = os.getcwd()
    # search from cwd
    if os.path.exists(root):
        return pwd, pwd
    if root in pwd:
        target_pwd = pwd[:pwd.index(root)]
    # search from the script path
    elif root in __file__:
        target_pwd = __file__[:__file__.index(root)]
    else:
        raise FileNotFoundError(f"Error: {root} not found in the path")
    os.chdir(target_pwd)
    print (f"Working directory: {target_pwd}")
    return target_pwd, pwd

if __name__ == "__main__":
    setting_file = SETTING_FILE
    if len(sys.argv) > 1:
        setting_file = sys.argv[1]

    # load the settings file
    settings = load_settings(setting_file)
    change_pwd_to_script_root()
    # replace settings in place
    for config in settings.keys():
        if config.endswith(".xml"):
            replace_value_in_xml(os.path.join(XML_PATH, config), settings[config])
        elif config.endswith(".py"):
            replace_value_in_py(os.path.join(KEY_SETTINGS_PATH, config), settings[config])
        else:
            raise ValueError(f"Error: {config} is not a supported configuration")
    print("Done")
