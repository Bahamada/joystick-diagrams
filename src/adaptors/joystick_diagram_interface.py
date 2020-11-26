import functions.helper as helper
from abc import ABC, abstractmethod


class JDInterface(ABC):
    no_bind_text: str
    joystick_dictionary: dict[str, dict[str, dict]]

    def __init__(self):
        self.no_bind_text = "NO BIND"
        self.joystick_dictionary = {}

    @abstractmethod
    def get_device_names(self) -> list[str]:
        ...

    @abstractmethod
    def get_modes(self) -> list[str]:
        ...

    def update_joystick_dictionary(self, device: str, mode: str, inherit: object, buttons: object) -> None:
        data = {
            "Buttons": buttons,
            "Axis": "",
            "Inherit": inherit}

        if device in self.joystick_dictionary:
            if mode in self.joystick_dictionary[device]:
                self.joystick_dictionary[device][mode].update(data)
            else:
                self.joystick_dictionary[device].update({
                    mode: data
                })
        else:
            self.joystick_dictionary.update({
                device: {
                    mode: data
                }
            })

    def inherit_joystick_dictionary(self) -> None:
        for item in self.joystick_dictionary:
            for profile in self.joystick_dictionary[item]:
                if self.joystick_dictionary[item][profile]['Inherit']:
                    helper.log(f"{item} Profile has inheritance in mode {profile}", 'debug')
                    helper.log(f"Profile inherits from {self.joystick_dictionary[item][profile]['Inherit']}", 'debug')
                    inherit = self.joystick_dictionary[item][profile]['Inherit']
                    inherited_profile = self.joystick_dictionary[item][inherit]
                    helper.log("Inherited Profile Contains {}".format(inherited_profile), 'debug')
                    helper.log(f"Starting Profile Contains {self.joystick_dictionary[item][profile]['Buttons']}",
                               'debug')
                    for button, desc in inherited_profile['Buttons'].items():
                        check_button = button in self.joystick_dictionary[item][profile]['Buttons']
                        if not check_button:
                            self.joystick_dictionary[item][profile]['Buttons'].update({
                                button: desc
                            })
                        elif self.joystick_dictionary[item][profile]['Buttons'][button] == self.no_bind_text:
                            self.joystick_dictionary[item][profile]['Buttons'][button] = desc
                    helper.log(f"Ending Profile Contains {self.joystick_dictionary[item][profile]['Buttons']}", 'debug')
