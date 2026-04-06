import random
import math
from typing import List
from turtle_sim.core import Turtle, Pose, Velocity
from turtle_comm.comm import RabbitMQManager, ConsumerThread
from turtle_comm.messages import PoseMessage, VelocityMessage, SpawnMessage, SpawnAckMessage

class SimulationController:
    def __init__(self, rabbit_manager: RabbitMQManager, consumer_thread: ConsumerThread, world_width: float = 11.0, world_height: float = 11.0):
        self.world_width = world_width
        self.world_height = world_height
        self.turtles: List[Turtle] = []

        self.rabbit_manager = rabbit_manager
        self.consumer_thread = consumer_thread
        self.consumer_thread.add_subscription("/spawn", self._on_spawn)

    def _wall_hit_handler(self, turtle_name, wall_side):
        print(f"{turtle_name} hit the {wall_side} wall!")

    def move_turtles(self, dt: float):
        for turtle in self.turtles:
            turtle.pose.x += turtle.velocity.linear * dt * math.cos(turtle.pose.theta)
            turtle.pose.y += turtle.velocity.linear * dt * math.sin(turtle.pose.theta)
            turtle.pose.theta += turtle.velocity.angular * dt
            turtle.pose.theta = math.atan2(math.sin(turtle.pose.theta), math.cos(turtle.pose.theta))
            
            wall_hit = None
            if turtle.pose.x <= 0:
                turtle.pose.x = 0
                wall_hit = "left"
            elif turtle.pose.x >= self.world_width:
                turtle.pose.x = self.world_width
                wall_hit = "right"
            if turtle.pose.y <= 0:
                turtle.pose.y = 0
                wall_hit = "bottom"
            elif turtle.pose.y >= self.world_height:
                turtle.pose.y = self.world_height
                wall_hit = "top"
            
            if wall_hit:
                self._wall_hit_handler(turtle.name, wall_hit)

    def add_turtle(self, name, x, y, theta=0.0):
        if name in [t.name for t in self.turtles]:
            print(f"Turtle {name} already exists")
            return
        turtle = Turtle(name, Pose(x, y, theta), Velocity())
        self.turtles.append(turtle)
        self.consumer_thread.add_subscription(f"{name}/cmd_vel", self._make_cmd_vel_callback(name))
        print(f"Added turtle {name} at ({x:.1f},{y:.1f})")

    def set_cmd_vel(self, name, linear, angular):
        for t in self.turtles:
            if t.name == name:
                t.velocity.linear = linear
                t.velocity.angular = angular
                break

    def publish_cmd_vel(self, turtle_name, linear, angular):
        vel_msg = VelocityMessage(linear, angular)
        self.rabbit_manager.publish(f"{turtle_name}/cmd_vel", vel_msg.to_dict())

    def publish_all_poses(self):
        for turtle in self.turtles:
            pose_msg = PoseMessage(turtle.pose.x, turtle.pose.y, turtle.pose.theta)
            self.rabbit_manager.publish(f"{turtle.name}/pose", pose_msg.to_dict())

    def _make_cmd_vel_callback(self, turtle_name):
        def cb(routing_key, data):
            vel = VelocityMessage.from_dict(data)
            self.set_cmd_vel(turtle_name, vel.linear, vel.angular)
        return cb

    def _on_spawn(self, routing_key, data):
        spawn = SpawnMessage.from_dict(data)
        name = spawn.name
        if name in [t.name for t in self.turtles]:
            print(f"Spawn ignored: {name} already exists")
            return
        x = spawn.x if spawn.x != 0.0 else random.uniform(1.0, self.world_width-1)
        y = spawn.y if spawn.y != 0.0 else random.uniform(1.0, self.world_height-1)
        self.add_turtle(name, x, y, spawn.theta)

        ack = SpawnAckMessage(name, success=True)
        self.rabbit_manager.publish("/spawned", ack.to_dict())
        print(f"Published spawn ack for {name}")

    def stop(self):
        self.consumer_thread.stop()
        self.rabbit_manager.close()