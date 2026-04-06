import math
import time
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QPainter, QBrush, QColor, QPen

from turtle_sim.core.simulation_controller import SimulationController
from turtle_sim.ui.keyboard_controller import KeyboardController

class SimulatorWidget(QWidget):
    def __init__(self, controller: SimulationController, keyboard_controller: KeyboardController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.keyboard_controller = keyboard_controller

        self.setMinimumSize(600, 600)
        self.setFocusPolicy(Qt.StrongFocus)

        self.world_width = controller.world_width
        self.world_height = controller.world_height

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer)
        self.timer.start(50)
        self._last_time = None

    def _on_timer(self):
        now = time.time()
        if self._last_time is None:
            self._last_time = now
            return
        dt = min(0.05, now - self._last_time)
        if dt <= 0:
            self._last_time = now
            return

        self.controller.move_turtles(dt)
        self.controller.publish_all_poses()

        self._last_time = now
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(200, 240, 200))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(self._map_rect(0, 0, self.world_width, self.world_height))

        for turtle in self.controller.turtles:
            x, y, theta = turtle.pose.x, turtle.pose.y, turtle.pose.theta
            sx, sy = self._map_point(x, y)
            size = 20
            painter.save()
            painter.translate(sx, sy)
            painter.rotate(-math.degrees(theta))
            painter.setBrush(QBrush(Qt.blue if turtle.name == 'turtle1' else Qt.green))
            painter.setPen(QPen(Qt.black, 2))
            points = [
                QPointF(-size/2, -size/2),
                QPointF(size/2, 0),
                QPointF(-size/2, size/2)
            ]
            painter.drawPolygon(points)
            painter.restore()
            painter.drawText(sx - 15, sy - 10, turtle.name)

    def _map_point(self, x, y):
        w = self.width()
        h = self.height()
        margin = 30
        draw_w = w - 2*margin
        draw_h = h - 2*margin
        px = margin + (x / self.world_width) * draw_w
        py = margin + (1 - y / self.world_height) * draw_h
        return px, py

    def _map_rect(self, x0, y0, x1, y1):
        left_top = self._map_point(x0, y1)
        right_bottom = self._map_point(x1, y0)
        return QRectF(
            left_top[0], 
            left_top[1], 
            right_bottom[0] - left_top[0], 
            right_bottom[1] - left_top[1]
        )

    def keyPressEvent(self, event):
        if self.keyboard_controller.handle_key_press(event.key()):
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if self.keyboard_controller.handle_key_release(event.key()):
            return
        super().keyReleaseEvent(event)