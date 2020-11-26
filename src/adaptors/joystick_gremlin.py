'''Joystick Gremlin (Version ~13) XML Parser for use with Joystick Diagrams'''
import typing
from typing import Union, Tuple

from lxml import etree
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

import functions.helper as helper
import adaptors.joystick_diagram_interface as jdi


class JoystickGremlin(jdi.JDInterface):
    filepath: str
    devices: list[Element]
    deviceNames: list[str]
    device: Element
    tree: ElementTree

    def __init__(self, filepath):
        # TRY FIND PATH
        jdi.JDInterface.__init__(self)
        self.tree = self.parse_xml_file(filepath)

        # New Attributes
        self.devices = []
        self.deviceNames = []

    def get_device_names(self) -> list[str]:
        if not self.deviceNames:
            self.devices = self.get_devices()
            self.deviceNames = []
            for item in self.devices:
                self.deviceNames.append(item.attrib['name'])
        return self.deviceNames

    def get_modes(self) -> list[str]:
        self.devices = self.get_devices()
        profile_modes = []

        item = self.devices[0]  # All Modes common across JG
        modes = item.findall('mode')
        for mode in modes:
            mode_name = mode.attrib['name']
            profile_modes.append(mode_name)
        return profile_modes

    @staticmethod
    def parse_xml_file(xml_file) -> ElementTree:
        return etree.parse(xml_file)

    def create_dictionary(self, profiles: list[str] = None) -> dict[str, dict[str, dict]]:
        if profiles is None:
            profiles = []
        self.devices = self.get_devices()
        helper.log(f"Number of Devices: {len(self.devices)}", 'debug')

        using_inheritance = False
        for device in self.devices:
            current_device = device.attrib['name']
            modes = device.findall('mode')
            helper.log(f"All Modes: {list(map(lambda e: e.attrib['name'], modes))}")
            for mode in modes:
                current_inherit, using_inheritance = self.extract_inheritance(mode)
                current_mode = mode.attrib['name']
                helper.log(f"Selected Mode: {current_mode}", 'debug')
                buttons = mode.findall('button')
                button_array = self.extract_buttons(buttons)
                self.update_joystick_dictionary(current_device, current_mode, current_inherit, button_array)
        if using_inheritance:
            self.inherit_joystick_dictionary()
            self.filter_dictionary(profiles)
            return self.joystick_dictionary
        else:
            self.filter_dictionary(profiles)
            return self.joystick_dictionary

    # TODO: this dict needs better typing
    def filter_dictionary(self, profiles: list[str]) -> dict[str, dict[str, dict]]:
        if len(profiles) > 0:
            for key, value in self.joystick_dictionary.items():
                for item in value.copy():
                    if item not in profiles:
                        self.joystick_dictionary[key].pop(item, None)
        return self.joystick_dictionary

    def get_devices(self) -> list[Element]:
        if not self.devices:
            self.devices = self.tree.findall('.//device')
        return self.devices

    @staticmethod
    def extract_inheritance(mode: Element) -> Tuple[Union[bool, str], bool]:
        if 'inherit' not in mode.attrib or mode.attrib['inherit'] == '':
            return False, False
        return mode.attrib['inherit'], True

    def extract_buttons(self, buttons: list[Element]) -> dict[str, str]:
        button_array = {}
        for button in buttons:
            description = button.attrib.get('description', default=self.no_bind_text)
            if description == '':
                description = self.no_bind_text
            button_id = button.attrib['id']
            button_array[f"BUTTON_{button_id}"] = description
        return button_array

    def get_device_count(self) -> int:
        return len(self.get_devices())
