import logging
import time
from threading import Lock
from turtle_comm.comm import RabbitMQManager
from turtle_comm.messages import VelocityMessage, PoseMessage
from stalker.controller import StalkerController
from turtle_sim.core import Pose

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StalkerNode:
    def __init__(self, name: str, victim: str, speed: float, host: str):
        self.name = name
        self.victim = victim
        self.speed = speed
        self.manager = RabbitMQManager(host=host)
        self.victim_pose = None
        self.my_pose = None
        self._lock = Lock()
        self.running = True
        self.controller = StalkerController(speed=speed)

    def run(self):
        self.manager.connect()
        self.manager.start_consuming()

        self.manager.subscribe_json(f"{self.victim}/pose", self.on_victim_pose)
        self.manager.subscribe_json(f"{self.name}/pose", self.on_self_pose)

        logger.info(f"Stalker {self.name} started, following {self.victim}")

        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.manager.close()

    def on_victim_pose(self, routing_key: str, data: dict):
        pose_msg = PoseMessage.from_dict(data)
        with self._lock:
            self.victim_pose = Pose(pose_msg.x, pose_msg.y, pose_msg.theta)
        self._compute_and_publish()

    def on_self_pose(self, routing_key: str, data: dict):
        pose_msg = PoseMessage.from_dict(data)
        with self._lock:
            self.my_pose = Pose(pose_msg.x, pose_msg.y, pose_msg.theta)
        self._compute_and_publish()

    def _compute_and_publish(self):
        with self._lock:
            if self.victim_pose is None or self.my_pose is None:
                return
            linear, angular = self.controller.compute_velocity(self.my_pose, self.victim_pose)
            vel_msg = VelocityMessage(linear, angular)
        self.manager.publish_json(f"{self.name}/cmd_vel", vel_msg.to_dict())

    def stop(self):
        self.running = False