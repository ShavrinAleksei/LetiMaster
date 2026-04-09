from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Signal

class MainWindow(QMainWindow):
    closing = Signal()

    def __init__(self, central_widget):
        super().__init__()
        self.setWindowTitle("Turtle Simulator with RabbitMQ")
        self.setGeometry(100, 100, 800, 700)
        self.setCentralWidget(central_widget)

    def closeEvent(self, event):
        self.closing.emit()
        event.accept()