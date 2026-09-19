import time
import threading
import sys
import argparse
from dds_interface import DDSInterface
from dds_models import Pose, Twist
from stalker_logic import TurtleController


class StalkerNode:
    def __init__(self, stalker_name: str, victim_name: str, speed: float = 1.0):
        self.stalker_name = stalker_name
        self.victim_name = victim_name

        self.dds = DDSInterface()
        self.controller = TurtleController(speed=speed)

        self.current_pose = None
        self.target_pose = None

        self.cmd_pub = self.dds.create_publisher(f"/{stalker_name}/cmd_vel", Twist)

        self.dds.create_subscriber(f"/{stalker_name}/pose", Pose, self._pose_callback)
        self.dds.create_subscriber(f"/{victim_name}/pose", Pose, self._target_callback)

        self.running = True
        self.control_thread = threading.Thread(target=self._control_loop, daemon=True)

        print(f"{stalker_name} Преследует {victim_name} со скоростью {speed}")

    def _pose_callback(self, msg: Pose):
        self.current_pose = msg

    def _target_callback(self, msg: Pose):
        self.target_pose = msg

    def _control_loop(self):
        while self.running:
            if self.current_pose and self.target_pose:
                linear, angular = self.controller.compute_velocity(
                    self.current_pose, self.target_pose
                )
                twist = Twist()
                twist.linear_x = linear
                twist.angular_z = angular
                self.dds.publish(self.cmd_pub, twist)
            time.sleep(0.05)

    def start(self):
        self.control_thread.start()

    def stop(self):
        self.running = False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stalker', default='turtle2')
    parser.add_argument('--victim', default='turtle1')
    parser.add_argument('--speed', type=float, default=1.0)
    args = parser.parse_args()

    node = StalkerNode(args.stalker, args.victim, args.speed)
    node.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        node.stop()


if __name__ == '__main__':
    main()