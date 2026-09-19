import math
import random
import time
from typing import List, Optional
from turtle_sim.core import Turtle, Pose, Velocity
from turtle_comm.comm import RabbitMQManager
from turtle_comm.messages import PoseMessage, VelocityMessage, SpawnMessage, SpawnAckMessage

class SimulationController:
    def __init__(self, host: str, world_width: float = 11.0, world_height: float = 11.0):
        self.world_width = world_width
        self.world_height = world_height
        self.host = host
        self.turtles: List[Turtle] = []
        self.rabbit: Optional[RabbitMQManager] = None
        self._running = True

    def start(self):
        self.rabbit = RabbitMQManager(host=self.host)
        self.rabbit.connect()
        self.rabbit.start_consuming()
        self.rabbit.subscribe_json("/spawn", self._on_spawn)
        print("SimulationController started, waiting for spawn messages")

    def _on_spawn(self, routing_key: str, data: dict):
        spawn = SpawnMessage.from_dict(data)
        name = spawn.name
        if name in [t.name for t in self.turtles]:
            print(f"Spawn ignored: {name} already exists")
            return
        x = spawn.x if spawn.x != 0.0 else random.uniform(1.0, self.world_width - 1)
        y = spawn.y if spawn.y != 0.0 else random.uniform(1.0, self.world_height - 1)
        self.add_turtle(name, x, y, spawn.theta)

        ack = SpawnAckMessage(name, success=True)
        self.rabbit.publish_json("/spawned", ack.to_dict())
        print(f"Published spawn ack for {name}")

    def add_turtle(self, name: str, x: float, y: float, theta: float = 0.0):
        if name in [t.name for t in self.turtles]:
            print(f"Turtle {name} already exists")
            return
        turtle = Turtle(name, Pose(x, y, theta), Velocity())
        self.turtles.append(turtle)
        self.rabbit.subscribe_json(f"{name}/cmd_vel", self._make_cmd_vel_callback(name))
        print(f"Added turtle {name} at ({x:.1f},{y:.1f})")

    def _make_cmd_vel_callback(self, turtle_name: str):
        def callback(routing_key: str, data: dict):
            vel = VelocityMessage.from_dict(data)
            self.set_cmd_vel(turtle_name, vel.linear, vel.angular)
        return callback

    def set_cmd_vel(self, name: str, linear: float, angular: float):
        for t in self.turtles:
            if t.name == name:
                t.velocity.linear = linear
                t.velocity.angular = angular
                break

    def publish_cmd_vel(self, turtle_name: str, linear: float, angular: float):
        vel_msg = VelocityMessage(linear, angular)
        self.rabbit.publish_json(f"{turtle_name}/cmd_vel", vel_msg.to_dict())

    def move_turtles(self, dt: float):
        for turtle in self.turtles:
            turtle.pose.x += turtle.velocity.linear * dt * math.cos(turtle.pose.theta)
            turtle.pose.y += turtle.velocity.linear * dt * math.sin(turtle.pose.theta)
            turtle.pose.theta += turtle.velocity.angular * dt
            turtle.pose.theta = math.atan2(math.sin(turtle.pose.theta), math.cos(turtle.pose.theta))

            turtle.pose.x = max(0.0, min(turtle.pose.x, self.world_width))
            turtle.pose.y = max(0.0, min(turtle.pose.y, self.world_height))

            self._publish_pose(turtle)

    def _publish_pose(self, turtle: Turtle):
        pose_msg = PoseMessage(turtle.pose.x, turtle.pose.y, turtle.pose.theta)
        self.rabbit.publish_json(f"{turtle.name}/pose", pose_msg.to_dict())

    def stop(self):
        self._running = False
        if self.rabbit:
            self.rabbit.close()
        print("SimulationController stopped")