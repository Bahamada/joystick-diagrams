"""DCS World Lua Config Parser for use with Joystick Diagrams"""
import os
import re
from pathlib import Path
from typing import Union

import ply.lex as lex
import ply.yacc as yacc
import functions.helper as helper
import adaptors.joystick_diagram_interface as jdi
import adaptors.dcs_world_lex  # Do not remove - PLY production requirement
import adaptors.dcs_world_parse  # Do not remove - PLY production requirement


class DCSWorldParser(jdi.JDInterface):
    path: str
    remove_easy_modes: bool
    joystick_listing: dict
    profiles_to_process: list
    file: str
    profile_devices: list[str]
    base_directory: list[str]
    valid_profiles: list[str]
    __easy_mode: str

    def __init__(self, path: str, remove_easy_modes: bool = True):
        jdi.JDInterface.__init__(self)
        self.path: str = path
        self.remove_easy_modes: bool = remove_easy_modes
        self.joystick_listing: dict = {}
        self.profiles_to_process: list = []
        self.file: str = ''
        self.profile_devices: list[str] = []
        self.base_directory: list[str] = self.__validate_base_directory()
        self.valid_profiles: list[str] = self.__validate_profiles()
        self.__easy_mode: str = '_easy'

    def __validate_base_directory(self) -> list[str]:
        """validate the base directory structure, make sure there are files."""
        if 'Config' not in os.listdir(self.path):
            raise FileNotFoundError("DCS: No Config Folder found in DCS Folder.")
        try:
            return os.listdir(os.path.join(self.path, 'Config', 'Input'))
        except FileNotFoundError:
            raise FileNotFoundError("DCS: No input directory found")

    def __validate_profiles(self) -> list[str]:
        """
        Validate Profiles Routine
        """
        if len(self.base_directory) <= 0:
            raise FileExistsError("DCS: No profiles exist in Input directory!")
        valid_items: list[str] = []
        for item in self.base_directory:
            valid = self.__validate_profile(item)
            if not valid:
                helper.log("DCS: Profile {} has no joystick directory files".format(item))
                continue
            valid_items.append(item)

        return valid_items

    def __validate_profile(self, item: str) -> Union[list[str], bool]:
        """
        Validate Inidividual Profile
        Return Valid Profile
        """
        # TODO add additional checking for rogue dirs/no files etc
        if 'joystick' not in os.listdir(os.path.join(self.path, 'Config', 'Input', item)):
            return False
        return os.listdir(os.path.join(self.path, 'Config', 'Input', item, 'joystick'))

    def get_validated_profiles(self) -> list[str]:
        """ Expose Valid Profiles only to UI """
        if self.remove_easy_modes:
            return list(filter(lambda x: self.__easy_mode not in x, self.valid_profiles))
        return self.valid_profiles

    @staticmethod
    def convert_button_format(button: str) -> str:
        """ Convert DCS Buttons to match expected "BUTTON_X" format """
        return button.split('_')[1].replace("BTN", "BUTTON_")

    def process_profiles(self, profile_list: list[str] = None):
        if profile_list is None:
            profile_list = []
        if len(profile_list) > 0:
            self.profiles_to_process = profile_list
        else:
            self.profiles_to_process = self.get_validated_profiles()

        assert len(self.profiles_to_process) != 0, "DCS: There are no valid profiles to process"
        for profile in self.profiles_to_process:
            fq_path = os.path.join(self.path, 'Config', 'Input', profile, 'joystick')
            self.profile_devices = os.listdir(os.path.join(fq_path))
            self.joystick_listing = {}
            for item in self.profile_devices:
                # TODO: magic number
                self.joystick_listing.update({
                    item[:-48]: item
                })
            for joystick_device, joystick_file in self.joystick_listing.items():

                if os.path.isdir(os.path.join(fq_path, joystick_file)):
                    print("Skipping as Folder")
                    continue
                try:
                    self.file = Path(os.path.join(fq_path, joystick_file)).read_text(encoding="utf-8")
                    self.file = self.file.replace('local diff = ', '')  # CLEAN UP
                    self.file = self.file.replace('return diff', '')  # CLEAN UP
                except FileNotFoundError:
                    raise FileExistsError(
                        "DCS: File {} no longer found - It has been moved/deleted from directory".format(
                            joystick_file))
                data = self.parseFile()
                write_val = False
                button_array = {}
                if 'keyDiffs' in data.keys():
                    for value in data['keyDiffs'].values():
                        button = None
                        name = None
                        for item, attribute in value.items():
                            if item == 'name':
                                name = attribute
                            if item == 'added':
                                button = self.convert_button_format(attribute[1]['key'])
                                write_val = True
                        if write_val:
                            button_array.update({
                                button: name
                            })
                            write_val = False
                    self.update_joystick_dictionary(joystick_device, profile, False, button_array)
        return self.joystick_dictionary

    def parseFile(self):
        # pylint: disable=unused-variable
        tokens = (
            'LCURLY', 'RCURLY', 'STRING', 'NUMBER', 'LBRACE', 'RBRACE', 'COMMA', 'EQUALS', 'TRUE', 'FALSE',
            'DOUBLE_VAL')

        t_LCURLY = r"\{"
        t_RCURLY = r"\}"
        t_LBRACE = r"\["
        t_RBRACE = r"\]"
        t_COMMA = r"\,"
        t_EQUALS = r"\="

        def t_DOUBLE_VAL(t):
            r"(\+|\-)?[0-9]+\.[0-9]+"
            t.value = float(t.value)
            return t

        def t_NUMBER(t):
            r"[0-9]+"
            t.value = int(t.value)
            return t

        def t_STRING(t):
            r"\"[\w|\/|\(|\)|\-|\:|\+|\,|\&|\.|\'|\s]+\""
            t.value = t.value[1:-1]
            return t

        def t_TRUE(t):
            r'(true)'
            t.value = True
            return t

        def t_FALSE(t):
            r'(false)'
            t.value = False
            return t

        t_ignore = " \t\n"

        def t_error(t):
            print("Illegal character '%s'" % t.value[0])
            t.lexer.skip(1)

        # Parsing rules

        def p_dict(t):
            """dict : LCURLY dvalues RCURLY"""
            t[0] = t[2]

        def p_dvalues(t):
            """dvalues : dvalue
                    | dvalue COMMA
                    | dvalue COMMA dvalues"""
            t[0] = t[1]
            if len(t) == 4:
                t[0].update(t[3])

        def p_key_expression(t):
            """key : LBRACE NUMBER RBRACE
                | LBRACE STRING RBRACE"""
            t[0] = t[2]

        def p_value_expression(t):
            """ dvalue : key EQUALS STRING
            | key EQUALS boolean
            | key EQUALS DOUBLE_VAL
            | key EQUALS NUMBER
            | key EQUALS dict """
            t[0] = {t[1]: t[3]}

        def p_boolean(p):
            ''' boolean : TRUE
                        | FALSE
            '''
            p[0] = p[1]

        def p_error(t):
            print("Syntax error at '%s'" % t.value)

        # Build the lexer
        ## TODO: Consider env vars to run optimize=1 in deployed version
        lexer = lex.lex(
            debug=False,
            optimize=1,
            lextab='dcs_world_lex',
            reflags=re.UNICODE | re.VERBOSE
        )

        # Build the parser
        parser = yacc.yacc(
            debug=False,
            optimize=1,
            tabmodule='dcs_world_parse'
        )

        # Parse the data
        data = None
        try:
            data = parser.parse(self.file)
        except Exception as error:
            print(error)
        return data
