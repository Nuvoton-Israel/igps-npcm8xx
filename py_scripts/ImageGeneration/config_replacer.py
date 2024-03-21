import xml.etree.ElementTree as ET
import json
import os

XML_PATH = os.path.join("py_scripts","ImageGeneration","inputs")
SETTING_FILE =  os.path.join(XML_PATH, "settings.json")

"""
This function loads the settings file and checks if the file exists and is not empty
@param file: the settings file to load
@throws ValueError: if the file doesn't exist or is empty

@return: the settings dictionary
example of the settings file:
{
    "BootBlockAndHeader.xml":
    {
        "MC_CONFIG": "0x05"
    }
}
"""
def load_settings(file = SETTING_FILE):
    if os.path.isfile(file) == False:
        raise ValueError(f"Error: {file} doesn't exist")
    with open(file) as f:
        settings = json.load(f)
    if settings is None:
        raise ValueError("Error: settings file is empty")
    # check key (file) is valid
    for key in settings.keys():
        if os.path.isfile(os.path.join(XML_PATH, key)) == False:
            raise ValueError(f"Error: file {key} doesn't exist")
    return settings

def replace_value_in_xml(xml_file, dict, target_xml = None):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    # we only interested in the BinField elements
    elements = root.findall('BinField')
    # replace all the value pairs we defined
    for tag, value in dict.items():
        # search all the elements
        search_count = 0
        for element in elements:
            e = element.find('name')
            if e is not None and e.text is not None and e.text == tag:
                c = element.find('content')
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

if __name__ == "__main__":
    # do nothing if the settings file doesn't exist
    if os.path.isfile(SETTING_FILE) == False:
        exit(0)
    # load the settings file
    settings = load_settings()
    # test the function
    for xml in settings.keys():
        # replace_value_in_xml(os.path.join(XML_PATH, xml), settings[xml], os.path.join("test", xml))
        replace_value_in_xml(os.path.join(XML_PATH, xml), settings[xml])
    # test fail case
    #replace_value_in_xml(xml, {"test": "test_value"})
