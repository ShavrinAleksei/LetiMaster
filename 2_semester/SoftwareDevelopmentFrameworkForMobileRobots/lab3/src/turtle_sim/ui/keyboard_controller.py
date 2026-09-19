from PySide6.QtCore import QObject

class KeyboardController(QObject):
    def __init__(self, controller, turtle_name: str, key_map: dict, stop_velocity=(0.0, 0.0)):
        super().__init__()
        self.controller = controller
        self.turtle_name = turtle_name
        self.key_map = key_map
        self.stop_velocity = stop_velocity
        self.pressed_keys = set()

    def handle_key_press(self, key):
        if key in self.key_map:
            self.pressed_keys.add(key)
            self._update_velocity()
            return True
        return False

    def handle_key_release(self, key):
        if key in self.key_map:
            self.pressed_keys.discard(key)
            self._update_velocity()
            return True
        return False
    
    def _update_velocity(self):
        total_linear = 0.0
        total_angular = 0.0
        for key in self.pressed_keys:
            linear, angular = self.key_map[key]
            total_linear += linear
            total_angular += angular

        self.controller.publish_cmd_vel(self.turtle_name, total_linear, total_angular)