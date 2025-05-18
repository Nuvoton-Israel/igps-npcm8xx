# SPDX-License-Identifier: GPL-2.0
#
# Nuvoton IGPS: Image Generation And Programming Scripts For Arbel BMC
#
# Copyright (C) 2024 Nuvoton Technologies, All Rights Reserved
#-------------------------------------------------------------------------

"""
Usage:
    python config_replacer.py settings.json
    Please note the working directory should be the root of the project.
    example:
        python py_scripts/ImageGeneration/config_replacer.py
            py_scripts/ImageGeneration/inputs/settings.json
Test:
    python py_scripts/ImageGeneration/test_config_replacer.py

This script is used for replacing the settings in the XML and Python files from
Openbmc setting file. It would be useful to reduce effort of maintaining full
XML for each configuration.
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


def is_in_instance(value, types):
    """
    Check if the value is in the instance of the types.

    Args:
        value: The value to check.
        types: The types to check against.

    Returns:
        bool: True if the value is in the instance of the types, False otherwise.
    """
    for type in types:
        if isinstance(value, type):
            return True
    return False


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
    if not os.path.isfile(file):
        raise FileNotFoundError(f"Error: {file} doesn't exist")
    # we should accept empty settings file or {} as valid
    settings = {}
    with open(file) as f:
        data = f.read().strip()
        if len(data) > 0:
            settings = json.loads(data)

    # remove comments
    def remove_comment(d: dict):
        if "//" in d:
            del d["//"]
        if "comment" in d:
            del d["comment"]

    def raise_err(config: str, key: str):
        raise ValueError(
                 f"Error: Invalid format in settings file for {config}:{key}")
    remove_comment(settings)
    # check settings format
    for config in list(settings.keys()):
        values = settings[config]
        if not isinstance(values, dict):
            raise ValueError(f"Error: Invalid format in settings file for {config}")
        remove_comment(settings[config])
        if len(settings[config]) == 0:
            del settings[config]
            continue
        for key, value in values.items():
            # key should be str
            if not isinstance(key, str):
                raise_err(config, key)
            # we allow the value in json get more type
            elif config.endswith("json"):
                if not is_in_instance(value, (str, int, dict, list, bool)):
                    raise_err(config, key)
            else:
                if not isinstance(value, str):
                    raise_err(config, key)
    print("Settings format is valid")
    return settings


def replace_value_in_xml(xml_file: str, dict: dict[str, str], target: str = None):
    """
    Replaces the values in the specified XML file with the given dictionary.

    Args:
        xml_file (str): The path to the XML file.
        dict (dict[str, str]):
            The dictionary containing the tag-value pairs to replace.
        target (str, optional): The path to the target XML file.
            If not provided, the original XML file will be overwritten.

    Raises:
        ValueError: If a tag is not found in the XML file.

    Example:
        replace_value_in_xml("input.xml",
            {"TAG1": "VALUE1", "TAG2": "VALUE2"}, "output.xml")
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
            raise ValueError(f"Error: TAG \"{tag}\" not found in the xml file")
    # write the xml file
    if target is None:
        target = xml_file
    tree.write(target, "UTF-8", True)


class NoSectionConfigParser:
    """
    Hacks class for ConfigParser to avoid read/write section in the
    configuration file.
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
        dict (dict[str, str]):
            The dictionary containing the key-value pairs to replace.
        target_py (str, optional): The path to the target Python file. If not
         provided, the original Python file will be overwritten.

    Raises:
        ValueError: If a key is not found in the configuration file.

    Example:
        replace_value_in_py("script.py",
            {"KEY1": "VALUE1", "KEY2": "VALUE2"}, "output.py")
    """
    cp = NoSectionConfigParser()
    cp.read(py_file)
    for key, value in dict.items():
        cp.set(key, value)
    if target_py is not None:
        cp.write(target_py)
    else:
        cp.write(py_file)


def replace_settings_in_json(file: str, settings: dict, target: str = None):
    with open(file, "r") as f:
        data = json.load(f)

    # modify data if settings keys are in the data
    # assume we have two levels of data
    # the first level is the key in the settings file
    for key, value in settings.items():
        if key in data:
            # check if the value is a dict
            if isinstance(value, dict):
                # replace the value in the settings
                for sub_key, sub_value in value.items():
                    if sub_key in data[key]:
                        print("replacing {}.{} value {} to {}".format(
                                key, sub_key, data[key][sub_key], sub_value))
                        data[key][sub_key] = sub_value
                    else:
                        raise ValueError(
                            f"Error: {sub_key} not found in the settings file")
            else:
                # replace the value in the settings
                if key == "COMBO1_OFFSET":
                    # check if the value is a String
                    if isinstance(value, str):
                        value = eval(value)
                print(f"replacing {key} value {data[key]} to {value}")
                data[key] = value
        else:
            raise ValueError(f"Error: {key} not found in the settings file")
    # write the data to the target file
    if target is None:
        target = file
    with open(target, "w") as f:
        json.dump(data, f, indent=4)


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
        elif config.endswith(".json"):
            replace_settings_in_json(
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
    print(f"Working directory: {target_pwd}")
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
            replace_value_in_py(os.path.join(KEY_SETTINGS_PATH, config),
                                settings[config])
        elif config.endswith(".json"):
            replace_settings_in_json(os.path.join(KEY_SETTINGS_PATH, config),
                                     settings[config])
        else:
            raise ValueError(f"Error: {config} is not a supported configuration")
    print("Done")
