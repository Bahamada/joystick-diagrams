from os import path
import os
from pathlib import Path
import re
import html
from typing import Any

import functions.helper as helper
from PyQt5 import QtWidgets

# TODO: use lxml
class Export:
    export_directory: str
    templates_directory: str
    file_name_divider: str
    joystick_listing: dict[str, dict[str, dict]]
    export_progress: str
    no_bind_text: str
    executor: str
    error_bucket: list

    def __init__(self, joystick_listing: dict[str, dict[str, dict]], parser_id: str = "UNKNOWN",
                 custom_no_bind: str = "No Bind"):
        self.export_directory = './diagrams/'
        self.templates_directory = './templates/'
        self.file_name_divider = "_"
        self.joystick_listing = joystick_listing
        self.export_progress = ''
        self.no_bind_text = custom_no_bind
        self.executor = parser_id
        self.error_bucket = []

    def export_config(self, progress_bar: QtWidgets.QProgressBar = None) -> list[str]:

        joystick_count = len(self.joystick_listing)

        progress_increment = 1

        if isinstance(progress_bar, QtWidgets.QProgressBar):
            progress_bar.setValue(0)
            progress_increment = 100 / joystick_count

        for joystick in self.joystick_listing:
            base_template = self.get_template(joystick)
            if base_template:
                progress_increment_modes = len(self.joystick_listing[joystick])
                for mode in self.joystick_listing[joystick]:
                    write_template = base_template
                    completed_template = self.replace_template_strings(joystick, mode, write_template)
                    completed_template = self.replace_unused_strings(completed_template)
                    completed_template = self.brand_template(mode, completed_template)
                    self.save_template(joystick, mode, completed_template)
                    if isinstance(progress_bar, QtWidgets.QProgressBar):
                        progress_bar.setValue(
                            int(progress_bar.value() + (progress_increment / progress_increment_modes)))
            else:
                self.error_bucket.append("No Template for: {}".format(joystick))

            if isinstance(progress_bar, QtWidgets.QProgressBar):
                progress_bar.setValue(progress_bar.value() + progress_increment)

        if isinstance(progress_bar, QtWidgets.QProgressBar):
            progress_bar.setValue(100)
        return self.error_bucket

    def update_progress(self) -> None:
        pass

    @staticmethod
    def create_directory(directory: str) -> bool:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                return True
            except PermissionError as e:
                helper.log(str(e), "error")
                raise
        else:
            return False

    def get_template(self, joystick: str) -> str:
        return self.get_template_from_dir(joystick, self.templates_directory)

    @staticmethod
    def get_template_from_dir(joystick: str, templates_directory: str) -> str:
        if path.exists(templates_directory + joystick + ".svg"):
            data = Path(os.path.join(templates_directory, joystick + ".svg")).read_text(encoding="utf-8")
            return data
        else:
            return "False"

    def save_template(self, joystick, mode, template):
        output_path = self.export_directory + self.executor + "_" + joystick + "_" + mode + ".svg"
        if not os.path.exists(self.export_directory):
            self.create_directory(self.export_directory)
        try:
            output_file = open(output_path, "w", encoding="UTF-8")
            output_file.write(template)
            output_file.close()
        except PermissionError as e:
            helper.log(str(e) + 'error')
            raise

    def replace_unused_strings(self, template):
        return self.replace_unused_strings_with_no_bind_text(template, self.no_bind_text)

    @staticmethod
    def replace_unused_strings_with_no_bind_text(template: str, no_bind_text: str) -> str:
        regex_search = "\\bButton_\\d+\\b"
        matches = re.findall(regex_search, template, flags=re.IGNORECASE)
        matches = list(dict.fromkeys(matches))
        for i in matches:
            search = "\\b" + i + "\\b"
            template = re.sub(search, html.escape(no_bind_text), template, flags=re.IGNORECASE)
        return template

    def replace_template_strings(self, device, mode, template):
        items = self.joystick_listing[device][mode]['Buttons'].items()
        return self.replace_template_strings_in_items(items, self.no_bind_text, template)

    @staticmethod
    def replace_template_strings_in_items(items: list[tuple[str, Any]], no_bind_text, template):
        for b, v in items:
            if v == "NO BIND":
                v = no_bind_text
            regex_search = "\\b" + b + "\\b"
            template = re.sub(regex_search, html.escape(str(v)), template, flags=re.IGNORECASE)
        return template

    @staticmethod
    def brand_template(title: str, template: str) -> str:
        template = re.sub("\\bTEMPLATE_NAME\\b", title, template)
        return template
