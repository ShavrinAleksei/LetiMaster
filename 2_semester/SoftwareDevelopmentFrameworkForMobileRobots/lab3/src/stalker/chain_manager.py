import random
from turtle_comm.comm import RabbitMQManager, ConsumerThread
from turtle_comm.messages import SpawnMessage, SpawnAckMessage
from stalker.node import StalkerNode
import time

class StalkerChainManager:
    def __init__(self, rabbit_manager: RabbitMQManager, victim_turtle: str, speed: float):
        self.rabbit = rabbit_manager
        self.speed = speed
        self.prev_turtle = victim_turtle
        self.nodes = {}
        self.main_consumer = None

    def start(self, num_followers: int):
        self.main_consumer = ConsumerThread(host=self.rabbit.host)
        self.main_consumer.start()

        self.main_consumer.add_subscription("/spawned", self._on_spawn_ack)
        time.sleep(0.5)
        for i in range(2, num_followers + 2):
            stalker_name = f"stalker_turtle{i}"
            x = random.uniform(1.0, 10.0)
            y = random.uniform(1.0, 10.0)
            spawn_msg = SpawnMessage(stalker_name, x, y, 0.0)
            self.rabbit.publish("/spawn", spawn_msg.to_dict())
            print(f"Spawn requested: {stalker_name} at ({x:.1f},{y:.1f})")

    def _on_spawn_ack(self, routing_key, data):
        print(f"StalkerChainManager: received ack on {routing_key} with data {data}")
        ack = SpawnAckMessage.from_dict(data)
        if not ack.success:
            print(f"Failed to spawn {ack.name}")
            return

        stalker_name = ack.name
        node = StalkerNode(stalker_name, self.prev_turtle, self.speed, self.rabbit)
        self.nodes[stalker_name] = node

        self.main_consumer.add_subscription(f"{stalker_name}/pose", node.on_self_pose)
        self.main_consumer.add_subscription(f"{self.prev_turtle}/pose", node.on_target_pose)

        print(f"Follower added: {stalker_name} follows {self.prev_turtle}")
        self.prev_turtle = stalker_name

    def stop(self):
        if self.main_consumer:
            self.main_consumer.stop()
        self.rabbit.close()