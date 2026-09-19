import sys
import signal
import argparse
from PySide6.QtWidgets import QApplication
from turtle_sim.core.simulation_controller import SimulationController
from turtle_sim.ui.simulator_widget import SimulatorWidget
from turtle_sim.ui.main_window import MainWindow
from turtle_sim.ui.keyboard_controller import KeyboardController

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--turtle-name', default='turtle1')
    parser.add_argument('--linear-speed', type=float, default=2.0)
    parser.add_argument('--angular-speed', type=float, default=2.0)
    parser.add_argument('--start-x', type=float, default=5.0)
    parser.add_argument('--start-y', type=float, default=5.0)
    parser.add_argument('--start-theta', type=float, default=0.0)
    args = parser.parse_args()

    controller = SimulationController(host=args.host, world_width=11.0, world_height=11.0)
    controller.start()
    controller.add_turtle(args.turtle_name, args.start_x, args.start_y, args.start_theta)

    key_map = {
        Qt.Key_Up: (args.linear_speed, 0.0),
        Qt.Key_W: (args.linear_speed, 0.0),
        Qt.Key_Down: (-args.linear_speed, 0.0),
        Qt.Key_S: (-args.linear_speed, 0.0),
        Qt.Key_Left: (0.0, args.angular_speed),
        Qt.Key_A: (0.0, args.angular_speed),
        Qt.Key_Right: (0.0, -args.angular_speed),
        Qt.Key_D: (0.0, -args.angular_speed),
    }
    keyboard_ctrl = KeyboardController(controller, args.turtle_name, key_map)

    app = QApplication(sys.argv)
    simulator = SimulatorWidget(controller, keyboard_ctrl)
    window = MainWindow(simulator)
    window.show()

    def shutdown():
        print("\nShutting down...")
        controller.stop()
        app.quit()

    signal.signal(signal.SIGINT, lambda sig, frame: shutdown())
    window.closing.connect(shutdown)

    sys.exit(app.exec())

if __name__ == '__main__':
    from PySide6.QtCore import Qt
    main()