import sys
import argparse
from turtle_comm.comm import RabbitMQManager, ConsumerThread
from turtle_sim.core.simulation_controller import SimulationController
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from turtle_sim.ui.simulator_widget import SimulatorWidget
from turtle_sim.ui.main_window import MainWindow
from turtle_sim.ui.keyboard_controller import KeyboardController

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--turtle-name', default='turtle1', help='Имя управляемой черепашки')
    parser.add_argument('--linear-speed', type=float, default=2.0, help='Линейная скорость при нажатии')
    parser.add_argument('--angular-speed', type=float, default=2.0, help='Угловая скорость при нажатии')
    parser.add_argument('--start-x', type=float, default=5.0, help='Начальная X координата')
    parser.add_argument('--start-y', type=float, default=5.0, help='Начальная Y координата')
    parser.add_argument('--start-theta', type=float, default=0.0, help='Начальная ориентация (радианы)')
    args = parser.parse_args()

    rabbit_manager = RabbitMQManager(host=args.host)
    consumer_thread = ConsumerThread(host=args.host)
    consumer_thread.start()

    controller = SimulationController(
        rabbit_manager=rabbit_manager,
        consumer_thread=consumer_thread,
        world_width=11.0,
        world_height=11.0
    )
    controller.add_turtle('turtle1', 5.0, 5.0, 0.0)

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
    window = MainWindow(controller, simulator)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()