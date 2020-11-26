'''Joystick Gremlin (Version ~13) XML Parser for use with Joystick Diagrams'''
import typing
from typing import Union
from xml.dom import minidom
from xml.dom.minidom import Document, NodeList, Element, Node

import functions.helper as helper
import adaptors.joystick_diagram_interface as jdi


#TODO: use lxml
class JoystickGremlin(jdi.JDInterface):
    filepath: str
    deviceNames: list[str]
    profiles: list[str]
    modes: NodeList
    mode: Element
    devices: NodeList
    device: Node
    currentDevice: typing.Optional[str]
    currentMode: typing.Optional[str]
    currentInherit: Union[bool, str, None]
    buttons: NodeList
    buttonArray: typing.Optional[dict]
    usingInheritance: bool
    file: Document

    def __init__(self, filepath):
        # TRY FIND PATH
        jdi.JDInterface.__init__(self)
        self.file = self.parse_xml_file(filepath)

        # New Attributes
        self.deviceNames = self.get_device_names()
        self.profiles = []
        self.modes = None
        self.mode = None
        self.devices = None
        self.device = None
        self.currentDevice = None
        self.currentMode = None
        self.currentInherit = None
        self.inherit = None
        self.buttons = None
        self.buttonArray = None
        self.inheritModes = {}
        self.usingInheritance = False

    def get_device_names(self) -> list[str]:
        self.devices = self.get_devices()
        device_items = []

        for item in self.devices:
            device_items.append(item.getAttribute('name'))
        return device_items

    def get_modes(self) -> NodeList:
        self.devices = self.get_devices()
        profile_modes = []

        item = self.devices[0]  # All Modes common across JG
        modes = item.getElementsByTagName('mode')
        for mode in modes:
            mode_name = mode.getAttribute('name')
            profile_modes.append(mode_name)
        return profile_modes

    @staticmethod
    def parse_xml_file(xml_file) -> Document:
        # Improve loading of file, checks for validity etc
        return minidom.parse(xml_file)

    def create_dictionary(self, profiles: list[str] = None) -> dict[str, dict[str, dict]]:
        if profiles is None:
            profiles = []
        self.profiles = profiles
        self.devices = self.get_devices()
        helper.log("Number of Devices: {}".format(str(self.devices.length)), 'debug')

        for self.device in self.devices:
            self.currentDevice = self.get_single_device()
            self.modes = self.get_device_modes()
            helper.log("All Modes: {}".format(self.modes))
            for self.mode in self.modes:
                self.currentInherit = self.has_inheritance()
                self.buttonArray = {}
                self.currentMode = self.get_single_mode()
                helper.log("Selected Mode: {}".format(self.currentMode), 'debug')
                self.buttons = self.get_mode_buttons()
                self.buttonArray = self.extract_buttons()
                self.update_joystick_dictionary(self.currentDevice,
                                                self.currentMode,
                                                self.currentInherit,
                                                self.buttonArray
                                                )
        if self.usingInheritance:
            self.inherit_joystick_dictionary()
            self.filter_dictionary()
            return self.joystick_dictionary
        else:
            self.filter_dictionary()
            return self.joystick_dictionary

    def filter_dictionary(self) -> dict[str, dict[str, dict]]:
        if len(self.profiles) > 0:
            for key, value in self.joystick_dictionary.items():
                for item in value.copy():
                    if not item in self.profiles:
                        self.joystick_dictionary[key].pop(item, None)
        return self.joystick_dictionary

    def get_devices(self) -> NodeList:
        return self.file.getElementsByTagName('device')

    def get_mode_buttons(self) -> NodeList:
        return self.mode.getElementsByTagName('button')

    def get_device_modes(self) -> NodeList:
        return self.device.getElementsByTagName('mode')

    def get_single_device(self) -> str:
        return self.device.getAttribute('name')

    def get_single_mode(self) -> str:
        return self.mode.getAttribute('name')

    def has_inheritance(self) -> Union[bool, str]:
        inherit = self.mode.getAttribute('inherit')
        if inherit != '':
            if not self.usingInheritance:
                self.usingInheritance = True
            return inherit
        else:
            return False

    def extract_buttons(self) -> dict:
        for i in self.buttons:
            if i.getAttribute('description') != "":
                self.buttonArray.update({
                    "BUTTON_" + str(i.getAttribute('id')): str(i.getAttribute('description'))
                })
            else:
                self.buttonArray.update({
                    "BUTTON_" + str(i.getAttribute('id')): self.no_bind_text
                })
        return self.buttonArray

    def get_device_count(self) -> int:
        return self.file.getElementsByTagName('device').length
