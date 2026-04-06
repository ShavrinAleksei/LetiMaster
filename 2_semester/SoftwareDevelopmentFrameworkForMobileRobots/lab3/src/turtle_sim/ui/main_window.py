from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QStatusBar
from turtle_sim.core.simulation_controller import SimulationController


class MainWindow(QMainWindow):
    def __init__(self, controller: SimulationController, central_widget: QWidget):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Turtle Simulator with RabbitMQ")
        self.setGeometry(100, 100, 800, 700)

        self.setCentralWidget(central_widget)

    def closeEvent(self, event):
        self.controller.stop()
        event.accept()