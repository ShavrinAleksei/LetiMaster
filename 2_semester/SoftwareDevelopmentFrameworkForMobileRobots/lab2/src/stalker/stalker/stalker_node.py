import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from turtlesim.msg import Pose
from geometry_msgs.msg import Twist
from .stalker_logic import TurtleController


class StalkerNode(Node):
    def __init__(self):
        super().__init__('stalker_node')
        
        self._stalker_name = self.declare_parameter('stalker_name', 'turtle2').get_parameter_value().string_value
        self._victim_name = self.declare_parameter('victim_name', 'turtle1').get_parameter_value().string_value
        speed = self.declare_parameter('speed', 1.0).get_parameter_value().double_value
        
        self._controller = TurtleController(speed=speed)
        
        self._current_pose = None
        self._target_pose = None

        self._vel_pub = self.create_publisher(Twist, f'/{self._stalker_name}/cmd_vel', 10)
        
        self._pose_sub = self.create_subscription(
            Pose, 
            f'/{self._stalker_name}/pose', 
            self._pose_callback, 
            10
        )
        
        self._target_sub = self.create_subscription(
            Pose, 
            f'/{self._victim_name}/pose', 
            self._target_callback, 
            10
        )
        
        self._timer_period = 0.05
        self._timer = self.create_timer(self._timer_period, self._chase)
        
        self.get_logger().info(f'{self._stalker_name} преследует {self._victim_name}')
    
    def _pose_callback(self, msg):
        self._current_pose = msg
    
    def _target_callback(self, msg):
        self._target_pose = msg
    
    def _chase(self):
        if self._current_pose and self._target_pose:
            linear, angular = self._controller.compute_velocity(self._current_pose, self._target_pose)
            twist = Twist()
            twist.linear.x = linear
            twist.angular.z = angular
            self._vel_pub.publish(twist)
        else:
            self.get_logger().debug('Ждем позиций...', throttle_duration_sec=2.0)


def main(args=None):
    rclpy.init(args=args)
    stalker_node = StalkerNode()
    rclpy.spin(stalker_node)
    stalker_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
