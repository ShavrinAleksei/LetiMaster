import pygame
import math
import threading
import time
import os
from typing import Dict
import queue

os.environ.setdefault('CYCLONEDDS_INTERFACE', 'lo0')

from dds_interface import DDSInterface
from dds_models import Pose, Twist, Spawn


class Turtle:
    def __init__(self, name: str, x: float, y: float, theta: float = 0.0):
        self.name = name
        self.x = x
        self.y = y
        self.theta = theta
        self.linear_vel = 0.0
        self.angular_vel = 0.0


class TurtleSimNode:
    def __init__(self, width: int = 800, height: int = 600):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("DDS TurtleSim")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)

        self.dds = DDSInterface()
        self.turtles: Dict[str, Turtle] = {}
        self.pose_pubs = {}
        self.spawn_queue = queue.Queue()

        self.colors = [
            (255, 100, 100), (100, 255, 100), (100, 100, 255),
            (255, 255, 100), (255, 100, 255), (100, 255, 255),
        ]

        self._spawn_turtle("turtle1", 0.0, 0.0, 0.0)
        self.dds.create_subscriber("/spawn", Spawn, self._handle_spawn)

        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()

    def _spawn_turtle(self, name: str, x: float, y: float, theta: float):
        if name in self.turtles:
            return

        self.turtles[name] = Turtle(name, x, y, theta)
        self.pose_pubs[name] = self.dds.create_publisher(f"/{name}/pose", Pose)

        def cmd_callback(msg: Twist):
            if name in self.turtles:
                t = self.turtles[name]
                t.linear_vel = msg.linear_x
                t.angular_vel = msg.angular_z

        self.dds.create_subscriber(f"/{name}/cmd_vel", Twist, cmd_callback)

    def _handle_spawn(self, msg: Spawn):
        self.spawn_queue.put((msg.name, msg.x, msg.y, msg.theta))

    def _update_loop(self):
        last_time = time.time()

        while self.running:
            current_time = time.time()
            dt = min(current_time - last_time, 0.1)
            last_time = current_time

            try:
                while not self.spawn_queue.empty():
                    name, x, y, theta = self.spawn_queue.get_nowait()
                    self._spawn_turtle(name, x, y, theta)
            except queue.Empty:
                pass

            for name, turtle in self.turtles.items():
                if abs(turtle.linear_vel) > 0.01 or abs(turtle.angular_vel) > 0.01:
                    turtle.theta += turtle.angular_vel * dt
                    turtle.x += turtle.linear_vel * math.cos(turtle.theta) * dt
                    turtle.y += turtle.linear_vel * math.sin(turtle.theta) * dt
                    turtle.theta = math.atan2(math.sin(turtle.theta), math.cos(turtle.theta))

                pose = Pose(x=turtle.x, y=turtle.y, theta=turtle.theta, name=name)
                self.dds.publish(self.pose_pubs[name], pose)

            time.sleep(0.05)

    def draw(self):
        self.screen.fill((255, 255, 255))

        for i in range(0, self.width, 50):
            pygame.draw.line(self.screen, (220, 220, 220), (i, 0), (i, self.height))
        for i in range(0, self.height, 50):
            pygame.draw.line(self.screen, (220, 220, 220), (0, i), (self.width, i))

        for i, (name, turtle) in enumerate(self.turtles.items()):
            color = self.colors[i % len(self.colors)]
            screen_x = int(turtle.x * 30 + self.width // 2)
            screen_y = int(self.height // 2 - turtle.y * 30)

            pygame.draw.circle(self.screen, color, (screen_x, screen_y), 15)
            pygame.draw.circle(self.screen, (0, 0, 0), (screen_x, screen_y), 15, 2)

            end_x = screen_x + int(18 * math.cos(turtle.theta))
            end_y = screen_y - int(18 * math.sin(turtle.theta))
            pygame.draw.line(self.screen, (0, 0, 0), (screen_x, screen_y), (end_x, end_y), 3)

            text = self.font.render(name, True, (0, 0, 0))
            self.screen.blit(text, (screen_x - 25, screen_y - 30))

        info = self.font.render(f"Turtles: {len(self.turtles)}", True, (100, 100, 100))
        self.screen.blit(info, (10, self.height - 30))
        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.running = False
            self.draw()
            self.clock.tick(60)

        pygame.quit()


if __name__ == '__main__':
    TurtleSimNode().run()