import threading
from turtle_comm.comm import RabbitMQManager
from turtle_comm.messages import VelocityMessage, PoseMessage
from stalker.controller import StalkerController
from turtle_sim.core import Pose

class StalkerNode:
    def __init__(self, stalker_name: str, victim_name: str, speed: float, rabbit_manager: RabbitMQManager):
        self.stalker_name = stalker_name
        self.victim_name = victim_name
        self.rabbit_manager = rabbit_manager
        self.controller = StalkerController(speed=speed)

        self._current_pose = None
        self._target_pose = None
        self._lock = threading.Lock()

    def on_self_pose(self, routing_key, data):
        pose_msg = PoseMessage.from_dict(data)
        with self._lock:
            self._current_pose = Pose(pose_msg.x, pose_msg.y, pose_msg.theta)
        self._try_chase()

    def on_target_pose(self, routing_key, data):
        pose_msg = PoseMessage.from_dict(data)
        with self._lock:
            self._target_pose = Pose(pose_msg.x, pose_msg.y, pose_msg.theta)
        self._try_chase()

    def _try_chase(self):
        with self._lock:
            if self._current_pose is None or self._target_pose is None:
                return
            current = self._current_pose
            target = self._target_pose
        linear, angular = self.controller.compute_velocity(current, target)
        vel_msg = VelocityMessage(linear, angular)
        self.rabbit_manager.publish(f"{self.stalker_name}/cmd_vel", vel_msg.to_dict())